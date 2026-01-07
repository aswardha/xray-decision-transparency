from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

# Database setup imports
# - Base: SQLAlchemy declarative base (all models inherit from this)
# - engine: database engine (Postgres / SQLite / etc.)
# - SessionLocal: factory to create DB sessions
from db import Base, engine, SessionLocal
from models import PipelineRun, Step          # ORM models representing DB tables
from schemas import RunSchema, QueryRequest   # Pydantic schemas used for request validation
from analysis import elimination_rate         # Analysis helper function used for metrics and debugging


# Create database tables on application startup.
# This ensures the DB schema exists before handling requests.
# In production, this would usually be handled via migrations.
Base.metadata.create_all(bind=engine)
app = FastAPI(title="X-Ray API")              # Create the FastAPI application instance


def get_db():
    
    # Dependency that provides a database session to each request.

    # FastAPI will:
    # - create a new DB session at request start
    # - inject it into the route handler
    # - guarantee it is closed after the request completes
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/v1/runs")
def ingest_run(run: RunSchema, db: Session = Depends(get_db)):
    
    # Ingest a complete pipeline run sent by the X-Ray SDK.

    # This endpoint:
    # - receives a full pipeline execution payload
    # - stores the run metadata
    # - stores all associated steps
    

    # Create a PipelineRun DB record from the incoming schema
    db_run = PipelineRun(
        run_id=run.run_id,
        pipeline_name=run.pipeline_name,
        context=run.context,
        success=run.success,
        total_duration_ms=run.total_duration_ms
    )

    db.add(db_run)          # Add the run record to the session

    # Store each step belonging to this run
    for step in run.steps:
        # step.dict() converts the Pydantic model into a plain dict
        # **step.dict() maps fields directly to ORM columns
        db.add(Step(**step.dict()))

    db.commit()    # Commit all changes in a single transaction

    return {
        "status": "success",
        "run_id": run.run_id
    }


@app.get("/api/v1/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    
    # Fetch a pipeline run and all its steps by run_id.

    # Used for:
    # - debugging
    # - UI display
    # - post-run inspection

    run = db.query(PipelineRun).filter_by(run_id=run_id).first()    # Fetch the pipeline run metadata
    steps = db.query(Step).filter_by(run_id=run_id).all()           # Fetch all steps belonging to the run

    return {
        "run": run,
        "steps": steps
    }


@app.post("/api/v1/runs/query")
def query_runs(query: QueryRequest, db: Session = Depends(get_db)):
    
    # Query runs based on step behavior.

    # This endpoint allows analytical queries like:
    # - find steps of a certain type
    # - detect steps with high elimination rates
    
    steps = db.query(Step).filter_by(step_type=query.step_type).all()      # Fetch all steps matching the requested step type

    results = []

    for step in steps:
        rate = elimination_rate(step)        # Calculate how many candidates were eliminated in this step

        # Compare against the user-provided threshold
        if rate >= query.min_candidates_eliminated_pct / 100:
            results.append({
                "run_id": step.run_id,
                "step_name": step.step_name,
                "elimination_rate": rate
            })

    return results


@app.get("/api/v1/debug/{run_id}")
def debug_run(run_id: str, db: Session = Depends(get_db)):
    
    # Debug endpoint to analyze step behavior for a single run.

    # Flags potentially problematic steps based on heuristics,
    # such as overly aggressive elimination.

    steps = db.query(Step).filter_by(run_id=run_id).all()      # Fetch all steps for the given run

    analysis = []

    for step in steps:
        rate = elimination_rate(step)
        flags = []

        # Example heuristic:
        # If more than 90% of candidates are eliminated,
        # mark this step as suspicious.
        if rate > 0.9:
            flags.append("HIGH_ELIMINATION")

        analysis.append({
            "step_name": step.step_name,
            "reduction_rate": rate * 100,
            "flags": flags
        })

    return {
        "run_id": run_id,
        "step_analysis": analysis
    }

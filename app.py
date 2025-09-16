import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import torch
from fastapi.middleware.cors import CORSMiddleware
import os

# Import the Recommender class from your src package
from src.inference import Recommender

# Initialize the FastAPI app
app = FastAPI(
    title="Spotify GNN Music Recommender API",
    description="An API to get song recommendations based on a playlist ID.",
    version="0.1.0"
)

# --- 1. Add CORS Middleware ---
# This allows your React front-end (running on a different port) to make requests to this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your front-end's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. Load the Recommender Model at Startup ---
# This global variable will hold our recommender instance.
recommender = None

@app.on_event("startup")
def load_model():
    """Load the recommender model into memory when the application starts."""
    global recommender
    try:
        # We assume the artifacts are in the 'artifacts' directory relative to the app's location
        artifact_path = os.path.join(os.path.dirname(__file__), 'artifacts')
        recommender = Recommender(artifact_dir=artifact_path)
    except Exception as e:
        print(f"FATAL: Could not load recommender model. Error: {e}")
        # In a real application, you might want to prevent the app from starting
        # if the model can't be loaded. For now, we set it to None.
        recommender = None

# --- 3. Define Request and Response Data Models ---
class RecommendationRequest(BaseModel):
    playlist_id: int
    page: int = 1
    page_size: int = 10

class Song(BaseModel):
    track_name_x: str
    artists: str

class RecommendationResponse(BaseModel):
    recommendations: list[Song]
    hasMore: bool

# --- 4. Create API Endpoints ---
@app.get("/")
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"message": "Welcome to the Music Recommender API. Navigate to /docs for the interactive API documentation."}

@app.post("/recommendations/", response_model=RecommendationResponse)
def get_recommendations(request: RecommendationRequest):
    """
    Takes a playlist ID and returns a paginated list of song recommendations.
    """
    if recommender is None:
        raise HTTPException(status_code=503, detail="Model is not available. Please check server logs.")

    try:
        # --- Get All Possible Recommendations ---
        # The underlying recommender logic calculates scores for all songs.
        # We'll get all of them and then slice for pagination.
        all_recs_df = recommender.get_recommendations(
            playlist_id=request.playlist_id,
            num_recommendations=500  # Fetch a large number to paginate from
        )

        if "error" in all_recs_df:
             raise HTTPException(status_code=404, detail=all_recs_df["error"])

        # --- Paginate the Results ---
        start_index = (request.page - 1) * request.page_size
        end_index = start_index + request.page_size
        
        paginated_recs = all_recs_df.iloc[start_index:end_index]
        
        # Determine if there are more pages
        has_more = end_index < len(all_recs_df)

        return {
            "recommendations": paginated_recs.to_dict('records'),
            "hasMore": has_more
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")

# --- 5. Run the API Server ---
if __name__ == "__main__":
    # This block allows you to run the app directly using `python app.py`
    # It will look for the uvicorn package in your virtual environment.
    uvicorn.run(app, host="0.0.0.0", port=8000)

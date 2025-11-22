"""Main FastAPI application for MTG Keep or Mull."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mtg_keep_or_mull.api.routers import decks, decisions, sessions, statistics

# Create FastAPI app
app = FastAPI(
    title="MTG Keep or Mull API",
    description=(
        "REST API for MTG mulligan practice simulator. "
        "Helps players train their mulligan decisions and track statistics.\n\n"
        "**Fan Content Notice:** MTG Keep or Mull is unofficial Fan Content permitted under "
        "the Fan Content Policy. Not approved/endorsed by Wizards. "
        "Portions of the materials used are property of Wizards of the Coast. "
        "©Wizards of the Coast LLC."
    ),
    version="0.1.0",
    contact={
        "name": "Vibe-Coder 1.z3r0",
        "email": "vibecoder.1.z3r0@gmail.com",
    },
    license_info={
        "name": "MIT / VCL-Experimental-v0.1",
        "url": "https://github.com/vibecoder-1z3r0/mtg-keep-or-mull/blob/main/LICENSE",
    },
)

# Add CORS middleware (allow all origins for now - restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(decks.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(statistics.router, prefix="/api/v1")
app.include_router(decisions.router, prefix="/api/v1")


@app.get("/", tags=["root"])
def root() -> dict:
    """Root endpoint with API information.

    Returns:
        API metadata and links
    """
    return {
        "name": "MTG Keep or Mull API",
        "version": "0.1.0",
        "description": "Mulligan practice simulator for Magic: The Gathering",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "fan_content_notice": (
            "MTG Keep or Mull is unofficial Fan Content permitted under the Fan Content Policy. "
            "Not approved/endorsed by Wizards. Portions of the materials used are property of "
            "Wizards of the Coast. ©Wizards of the Coast LLC."
        ),
    }


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy"}


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0

"""Deck management API endpoints."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from mtg_keep_or_mull.api.dependencies import get_datastore
from mtg_keep_or_mull.api.models import DeckListResponse, DeckResponse, DeckUploadRequest
from mtg_keep_or_mull.datastore import DataStore
from mtg_keep_or_mull.deck import Deck
from mtg_keep_or_mull.models import DeckData

router = APIRouter(prefix="/decks", tags=["decks"])


@router.post("", response_model=DeckResponse, status_code=201)
def upload_deck(
    request: DeckUploadRequest, datastore: DataStore = Depends(get_datastore)
) -> DeckResponse:
    """Upload a new deck in MTGO format.

    Args:
        request: Deck upload request with deck_text and optional deck_name
        datastore: DataStore dependency

    Returns:
        DeckResponse with deck information

    Raises:
        HTTPException: If deck parsing fails
    """
    try:
        # Parse deck from text
        deck = Deck.from_text(request.deck_text)

        # Use provided name or generate one
        deck_name = request.deck_name or f"deck_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        deck.deck_name = deck_name

        # Create DeckData for storage
        deck_id = f"{deck_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        deck_data = DeckData(
            deck_id=deck_id,
            deck_name=deck_name,
            main_deck=[card.name for card in deck._cards],
            sideboard=[card.name for card in deck.sideboard],
            total_games=0,
            format=request.format,
            archetype=request.archetype,
            colors=request.colors,
            tags=request.tags,
        )

        # Save to datastore
        datastore.save_deck(deck_data)

        # Return response
        return DeckResponse(
            deck_id=deck_id,
            deck_name=deck_name,
            main_deck_size=len(deck._cards),
            sideboard_size=len(deck.sideboard),
            created_at=datetime.now(),
            format=request.format,
            archetype=request.archetype,
            colors=request.colors,
            tags=request.tags,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse deck: {str(e)}") from e


@router.get("", response_model=DeckListResponse)
def list_decks(
    format: Optional[str] = None,
    archetype: Optional[str] = None,
    colors: Optional[str] = None,
    tags: Optional[str] = None,
    datastore: DataStore = Depends(get_datastore),
) -> DeckListResponse:
    """List all available decks, optionally filtered by format, archetype, colors, and/or tags.

    Args:
        format: Optional format filter (e.g., "Pauper") - matches if value in deck's format list
        archetype: Optional archetype filter (e.g., "Aggro") - matches if value in deck's archetype list
        colors: Optional colors filter (e.g., "U", "Grixis") - matches if value in deck's colors list
        tags: Optional tags filter (e.g., "burn") - matches if value in deck's tags list
        datastore: DataStore dependency

    Returns:
        DeckListResponse with list of matching decks
    """
    # Use filtered list if filters provided, otherwise list all
    deck_ids = datastore.list_decks_filtered(
        format=format, archetype=archetype, colors=colors, tags=tags
    )
    decks: List[DeckResponse] = []

    for deck_id in deck_ids:
        deck_data = datastore.load_deck(deck_id)
        if deck_data:
            decks.append(
                DeckResponse(
                    deck_id=deck_data.deck_id,
                    deck_name=deck_data.deck_name,
                    main_deck_size=len(deck_data.main_deck),
                    sideboard_size=len(deck_data.sideboard),
                    created_at=datetime.now(),  # TODO: Store creation time in DeckData
                    format=deck_data.format,
                    archetype=deck_data.archetype,
                    colors=deck_data.colors,
                    tags=deck_data.tags,
                )
            )

    return DeckListResponse(decks=decks, total=len(decks))


@router.get("/random", response_model=DeckResponse)
def get_random_deck(
    format: Optional[str] = None,
    archetype: Optional[str] = None,
    colors: Optional[str] = None,
    tags: Optional[str] = None,
    datastore: DataStore = Depends(get_datastore),
) -> DeckResponse:
    """Get a random deck, optionally filtered by format, archetype, colors, and/or tags.

    Args:
        format: Optional format filter (e.g., "Pauper") - matches if value in deck's format list
        archetype: Optional archetype filter (e.g., "Aggro") - matches if value in deck's archetype list
        colors: Optional colors filter (e.g., "U", "Grixis") - matches if value in deck's colors list
        tags: Optional tags filter (e.g., "burn") - matches if value in deck's tags list
        datastore: DataStore dependency

    Returns:
        DeckResponse for a random matching deck

    Raises:
        HTTPException: If no decks match the filters
    """
    deck_data = datastore.get_random_deck(
        format=format, archetype=archetype, colors=colors, tags=tags
    )

    if not deck_data:
        filter_msg = []
        if format:
            filter_msg.append(f"format={format}")
        if archetype:
            filter_msg.append(f"archetype={archetype}")
        if colors:
            filter_msg.append(f"colors={colors}")
        if tags:
            filter_msg.append(f"tags={tags}")
        filter_str = " and ".join(filter_msg) if filter_msg else "any criteria"
        raise HTTPException(
            status_code=404, detail=f"No decks available matching {filter_str}"
        )

    return DeckResponse(
        deck_id=deck_data.deck_id,
        deck_name=deck_data.deck_name,
        main_deck_size=len(deck_data.main_deck),
        sideboard_size=len(deck_data.sideboard),
        created_at=datetime.now(),
        format=deck_data.format,
        archetype=deck_data.archetype,
        colors=deck_data.colors,
        tags=deck_data.tags,
    )


@router.get("/{deck_id}", response_model=DeckResponse)
def get_deck(deck_id: str, datastore: DataStore = Depends(get_datastore)) -> DeckResponse:
    """Get information about a specific deck.

    Args:
        deck_id: Unique deck identifier
        datastore: DataStore dependency

    Returns:
        DeckResponse with deck information

    Raises:
        HTTPException: If deck not found
    """
    deck_data = datastore.load_deck(deck_id)
    if not deck_data:
        raise HTTPException(status_code=404, detail=f"Deck not found: {deck_id}")

    return DeckResponse(
        deck_id=deck_data.deck_id,
        deck_name=deck_data.deck_name,
        main_deck_size=len(deck_data.main_deck),
        sideboard_size=len(deck_data.sideboard),
        created_at=datetime.now(),  # TODO: Store creation time in DeckData
        format=deck_data.format,
        archetype=deck_data.archetype,
        colors=deck_data.colors,
        tags=deck_data.tags,
    )


@router.delete("/{deck_id}", status_code=204)
def delete_deck(deck_id: str, datastore: DataStore = Depends(get_datastore)) -> None:
    """Delete a deck.

    Args:
        deck_id: Unique deck identifier
        datastore: DataStore dependency

    Raises:
        HTTPException: If deck not found
    """
    deck_data = datastore.load_deck(deck_id)
    if not deck_data:
        raise HTTPException(status_code=404, detail=f"Deck not found: {deck_id}")

    # TODO: Implement delete method in DataStore
    # For now, we'll raise a 501 Not Implemented
    raise HTTPException(status_code=501, detail="Delete not yet implemented")


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0

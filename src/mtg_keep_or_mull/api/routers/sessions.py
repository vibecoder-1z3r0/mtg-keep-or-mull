"""Practice session API endpoints."""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from mtg_keep_or_mull.api.dependencies import (
    create_session_id,
    get_datastore,
    get_session_decks,
    get_sessions,
)
from mtg_keep_or_mull.api.models import (
    CardResponse,
    DecisionRequest,
    HandResponse,
    KeepHandRequest,
    SessionResponse,
    SessionStartRequest,
)
from mtg_keep_or_mull.card import Card
from mtg_keep_or_mull.datastore import DataStore
from mtg_keep_or_mull.deck import Deck
from mtg_keep_or_mull.hand import Hand
from mtg_keep_or_mull.models import HandDecisionData
from mtg_keep_or_mull.mulligan import MulliganSimulator

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _hand_to_response(hand: Hand) -> HandResponse:
    """Convert a Hand object to HandResponse.

    Args:
        hand: Hand object

    Returns:
        HandResponse
    """
    cards = [CardResponse(name=card.name) for card in hand.get_cards()]
    return HandResponse(cards=cards, size=hand.size(), signature=hand.get_signature())


@router.post("", response_model=SessionResponse, status_code=201)
def start_session(
    request: SessionStartRequest,
    datastore: DataStore = Depends(get_datastore),
    sessions: Dict[str, MulliganSimulator] = Depends(get_sessions),
    session_decks: Dict[str, str] = Depends(get_session_decks),
) -> SessionResponse:
    """Start a new mulligan practice session.

    Args:
        request: Session start request with deck_id and on_play
        datastore: DataStore dependency
        sessions: Active sessions dictionary
        session_decks: Session to deck mapping

    Returns:
        SessionResponse with session_id and opening hand

    Raises:
        HTTPException: If deck not found
    """
    # Load deck from datastore
    deck_data = datastore.load_deck(request.deck_id)
    if not deck_data:
        raise HTTPException(status_code=404, detail=f"Deck not found: {request.deck_id}")

    # Create Deck instance from DeckData
    cards = [Card(name) for name in deck_data.main_deck]
    deck = Deck(cards=cards)
    deck.deck_name = deck_data.deck_name
    deck.shuffle()

    # Create simulator
    simulator = MulliganSimulator(deck, on_play=request.on_play)

    # Draw opening hand
    hand = simulator.start_game()

    # Create session ID and store
    session_id = create_session_id()
    sessions[session_id] = simulator
    session_decks[session_id] = request.deck_id

    # Return response
    return SessionResponse(
        session_id=session_id,
        deck_id=request.deck_id,
        on_play=request.on_play,
        mulligan_count=0,
        current_hand=_hand_to_response(hand),
    )


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    sessions: Dict[str, MulliganSimulator] = Depends(get_sessions),
    session_decks: Dict[str, str] = Depends(get_session_decks),
) -> SessionResponse:
    """Get the current state of a practice session.

    Args:
        session_id: Unique session identifier
        sessions: Active sessions dictionary
        session_decks: Session to deck mapping

    Returns:
        SessionResponse with current session state

    Raises:
        HTTPException: If session not found
    """
    simulator = sessions.get(session_id)
    if not simulator:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    deck_id = session_decks[session_id]
    hand = simulator.get_current_hand()

    return SessionResponse(
        session_id=session_id,
        deck_id=deck_id,
        on_play=simulator.on_play,
        mulligan_count=simulator.get_mulligan_count(),
        current_hand=_hand_to_response(hand),
    )


@router.post("/{session_id}/mulligan", response_model=SessionResponse)
def mulligan_hand(
    session_id: str,
    sessions: Dict[str, MulliganSimulator] = Depends(get_sessions),
    session_decks: Dict[str, str] = Depends(get_session_decks),
) -> SessionResponse:
    """Mulligan the current hand.

    Args:
        session_id: Unique session identifier
        sessions: Active sessions dictionary
        session_decks: Session to deck mapping

    Returns:
        SessionResponse with new hand

    Raises:
        HTTPException: If session not found
    """
    simulator = sessions.get(session_id)
    if not simulator:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    deck_id = session_decks[session_id]

    # Take mulligan
    hand = simulator.mulligan()

    return SessionResponse(
        session_id=session_id,
        deck_id=deck_id,
        on_play=simulator.on_play,
        mulligan_count=simulator.get_mulligan_count(),
        current_hand=_hand_to_response(hand),
    )


@router.post("/{session_id}/keep", response_model=SessionResponse)
def keep_hand(
    session_id: str,
    request: KeepHandRequest,
    sessions: Dict[str, MulliganSimulator] = Depends(get_sessions),
    session_decks: Dict[str, str] = Depends(get_session_decks),
) -> SessionResponse:
    """Keep the current hand, bottoming cards if needed.

    Args:
        session_id: Unique session identifier
        request: Keep hand request with cards to bottom
        sessions: Active sessions dictionary
        session_decks: Session to deck mapping

    Returns:
        SessionResponse with final hand

    Raises:
        HTTPException: If session not found or invalid bottom cards
    """
    simulator = sessions.get(session_id)
    if not simulator:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    deck_id = session_decks[session_id]

    try:
        # Get current hand to find card objects
        current_hand = simulator.get_current_hand()
        hand_cards = current_hand.get_cards()

        # Convert card names to Card objects
        cards_to_bottom = []
        for card_name in request.cards_to_bottom:
            # Find the card in the hand
            matching_cards = [c for c in hand_cards if c.name == card_name]
            if not matching_cards:
                raise HTTPException(status_code=400, detail=f"Card not in hand: {card_name}")
            cards_to_bottom.append(matching_cards[0])
            # Remove from available cards to avoid duplicates
            hand_cards.remove(matching_cards[0])

        # Keep hand with bottomed cards
        final_hand = simulator.keep(cards_to_bottom)

        return SessionResponse(
            session_id=session_id,
            deck_id=deck_id,
            on_play=simulator.on_play,
            mulligan_count=simulator.get_mulligan_count(),
            current_hand=_hand_to_response(final_hand),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{session_id}/decision", status_code=201)
def record_decision(
    session_id: str,
    request: DecisionRequest,
    sessions: Dict[str, MulliganSimulator] = Depends(get_sessions),
    session_decks: Dict[str, str] = Depends(get_session_decks),
    datastore: DataStore = Depends(get_datastore),
) -> dict:
    """Record a mulligan decision for statistics.

    Args:
        session_id: Unique session identifier
        request: Decision request (keep or mull)
        sessions: Active sessions dictionary
        session_decks: Session to deck mapping
        datastore: DataStore dependency

    Returns:
        Success message

    Raises:
        HTTPException: If session not found
    """
    simulator = sessions.get(session_id)
    if not simulator:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    deck_id = session_decks[session_id]
    hand = simulator.get_current_hand()

    # Create decision data
    decision_data = HandDecisionData(
        hand_signature=hand.get_signature(),
        hand_display=[card.name for card in hand.get_cards()],
        mulligan_count=simulator.get_mulligan_count(),
        decision=request.decision,
        lands_in_hand=hand.count_lands(),
        on_play=simulator.on_play,
        timestamp=datetime.now(),
        deck_id=deck_id,
    )

    # Save to datastore
    datastore.save_hand_decision(decision_data)

    return {"message": "Decision recorded successfully"}


@router.delete("/{session_id}", status_code=204)
def end_session(
    session_id: str,
    sessions: Dict[str, MulliganSimulator] = Depends(get_sessions),
    session_decks: Dict[str, str] = Depends(get_session_decks),
) -> None:
    """End a practice session.

    Args:
        session_id: Unique session identifier
        sessions: Active sessions dictionary
        session_decks: Session to deck mapping

    Raises:
        HTTPException: If session not found
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")

    # Clean up session
    del sessions[session_id]
    del session_decks[session_id]


# AIA: Primarily AI, Human-initiated, Reviewed, Claude Code Web [Sonnet 4.5] v1.0

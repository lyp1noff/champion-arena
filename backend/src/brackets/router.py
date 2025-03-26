from fastapi import APIRouter, Depends

from src.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/brackets", tags=["Brackets"], dependencies=[Depends(get_current_user)]
)

mock_bracket = {
    "rounds": [
        {
            "round_number": 1,
            "matches": [
                {
                    "match_id": 1,
                    "athlete1": "qwe",
                    "athlete2": "ewq",
                    "winner": "qwe",
                },
                {
                    "match_id": 2,
                    "athlete1": "asd",
                    "athlete2": "asd",
                    "winner": None,
                },
            ],
        },
        {
            "round_number": 2,
            "matches": [
                {"match_id": 3, "athlete1": None, "athlete2": None, "winner": None}
            ],
        },
    ]
}


@router.get("/{bracket_id}")
def get_bracket_stub(bracket_id: int):
    return mock_bracket

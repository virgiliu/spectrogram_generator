from dataclasses import dataclass
from sqlmodel import Session
from app.models.audio import Audio


@dataclass
class AudioRepository:
    session: Session

    def create(self, audio: Audio) -> Audio:
        self.session.add(audio)
        self.session.commit()
        self.session.refresh(audio)
        return audio

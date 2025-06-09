from dataclasses import dataclass
from typing import Optional

from sqlmodel import Session, select

from app.models.audio import Audio
from app.models.constants import AUDIO_STATUS_DONE


@dataclass
class AudioRepository:
    session: Session

    def create(self, audio: Audio) -> Audio:
        self.session.add(audio)
        self.session.commit()
        self.session.refresh(audio)
        return audio

    def get_by_id(self, audio_id: int) -> Optional[Audio]:
        return self.session.exec(select(Audio).where(Audio.id == audio_id)).first()

    def mark_done(self, audio_id: int) -> None:
        audio = self.get_by_id(audio_id)
        if audio:
            audio.status = AUDIO_STATUS_DONE
            self.session.add(audio)
            self.session.commit()

from dataclasses import dataclass

from sqlmodel import Session, select

from app.models.audio import Audio


@dataclass
class AudioRepository:
    session: Session

    def create(self, audio: Audio) -> Audio:
        self.session.add(audio)
        self.session.commit()
        self.session.refresh(audio)
        return audio

    def get_by_id(self, audio_id: int) -> Audio:
        return self.session.exec(select(Audio).where(Audio.id == audio_id)).first()

    def mark_done(self, audio_id: int):
        audio = self.get_by_id(audio_id)
        if audio:
            audio.status = "done"
            self.session.add(audio)
            self.session.commit()

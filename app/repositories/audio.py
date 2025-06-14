from dataclasses import dataclass
from typing import Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.audio import Audio
from app.models.constants import AUDIO_STATUS_DONE


@dataclass
class AudioRepository:
    session: AsyncSession

    async def create(self, audio: Audio) -> Audio:
        self.session.add(audio)
        await self.session.commit()
        await self.session.refresh(audio)
        return audio

    async def get_by_id(self, audio_id: int) -> Optional[Audio]:
        result = await self.session.exec(select(Audio).where(Audio.id == audio_id))
        return result.first()

    async def mark_done(self, audio_id: int) -> None:
        audio = await self.get_by_id(audio_id)
        if audio:
            audio.status = AUDIO_STATUS_DONE
            self.session.add(audio)
            await self.session.commit()

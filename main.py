from fastapi import FastAPI, File, UploadFile
# import magic

app = FastAPI()

@app.get('/')
def health_check():
    return {"status": "ok"}
#
# @app.post('/upload')
# async def upload_audio(audio_file: UploadFile = File(...)):
#     file_content = audio_file.file.read(2048)
#     audio_file.file.seek(0)
#     mimetype = magic.from_buffer(file_content, mime=True)
#     return {"filename": audio_file.filename, "mimetype": mimetype}

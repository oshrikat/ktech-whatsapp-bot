from fastapi import FastAPI, Response
from controllers import webhook_controller

# אתחול האפליקציה עם שם גרסה מסודר שיופיע בתיעוד
app = FastAPI(title="K-tech WhatsApp Bot API", version="1.0")

# מחברים את ה-Controller שיצרנו לשרת המרכזי
app.include_router(webhook_controller.router)

@app.get("/privacy-policy")
async def privacy_policy():
    return Response(
        content="<h1>Privacy Policy</h1><p>This app is for personal development and testing purposes only. No user data is stored or shared.</p>", 
        media_type="text/html"
    )

@app.get("/")
async def root():
    return {"message": "K-tech Bot Server is running and listening!"}
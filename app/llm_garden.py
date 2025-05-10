from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate

load_dotenv()

def initialize_llm():
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    return llm

async def aexecute_chain(prompt_template, input_vars, parser=None):
        if parser:
            prompt_template += "\n {format_instructions} "
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=list(input_vars.keys()),
            partial_variables={} if parser is None else {"format_instructions": parser.get_format_instructions()}
        )
        llm = initialize_llm()
        chain = prompt | llm | (parser if parser else lambda x: x)
        response = await chain.ainvoke(input_vars)
        return response
    
def execute_chain(prompt_template, input_vars, parser=None):
        if parser:
            prompt_template += "\n {format_instructions} "
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=list(input_vars.keys()),
            partial_variables={} if parser is None else {"format_instructions": parser.get_format_instructions()}
        )
        llm = initialize_llm()
        chain = prompt | llm | (parser if parser else lambda x: x)
        response = chain.invoke(input_vars)
        if parser:
             return response
        return response.content

import json
hunk = """diff --git a/.env.template b/.env.template
index d7a7b7a3..ffbc3f05 100644
--- a/.env.template
+++ b/.env.template
@@ -31,3 +31,4 @@ ANTHROPIC_API_KEY=
 POSTHOG_API_KEY=
 POSTHOG_HOST=
 FIRECRAWL_API_KEY=
+API_KEY_SECRET_PREFIX=
diff --git a/app/api/router.py b/app/api/router.py
index aedbf623..9e4abf64 100644
--- a/app/api/router.py
+++ b/app/api/router.py
@@ -7,7 +7,7 @@
 from sqlalchemy.orm import Session
 
 from app.core.database import get_db
-from app.modules.auth.api_key_service import APIKeyService
+from app.modules.auth.api_key_service import APIKeyService, InvalidAPIKeyFormatError
 from app.modules.conversations.conversation.conversation_controller import (
     ConversationController,
 )
@@ -63,7 +63,15 @@ async def get_api_key_user(
             )
         return {"user_id": user.uid, "email": user.email, "auth_type": "api_key"}
 
-    user = await APIKeyService.validate_api_key(x_api_key, db)
+    try:
+        user = await APIKeyService.validate_api_key(x_api_key, db)
+    except InvalidAPIKeyFormatError:
+        raise HTTPException(
+            status_code=401,
+            detail="Invalid API key format",
+            headers={"WWW-Authenticate": "ApiKey"},
+        )
+
     if not user:
         raise HTTPException(
             status_code=401,
diff --git a/app/modules/auth/api_key_service.py b/app/modules/auth/api_key_service.py
index 4d6deb8a..5ff50e3b 100644
--- a/app/modules/auth/api_key_service.py
+++ b/app/modules/auth/api_key_service.py
@@ -10,10 +10,23 @@
 
 from app.modules.users.user_model import User
 from app.modules.users.user_preferences_model import UserPreferences
+from google.api_core.exceptions import NotFound
+
+
+class APIKeyServiceError(Exception):
+
+
+class InvalidAPIKeyFormatError(APIKeyServiceError):
+
+
+class APIKeyNotFoundError(APIKeyServiceError):
 
 
 class APIKeyService:
-    SECRET_PREFIX = "sk-"
+    SECRET_PREFIX = os.getenv("API_KEY_SECRET_PREFIX", "sk-")
     KEY_LENGTH = 32
 
     @staticmethod
@@ -98,10 +111,12 @@ async def create_api_key(user_id: str, db: Session) -> str:
         return api_key
 
     @staticmethod
-    async def validate_api_key(api_key: str, db: Session) -> Optional[dict]:
+    async def validate_api_key(api_key: str, db: Session) -> dict:
         if not api_key.startswith(APIKeyService.SECRET_PREFIX):
-            return None
+            raise InvalidAPIKeyFormatError(
+                "API key format is invalid. Expected prefix missing."
+            )
 
         hashed_key = APIKeyService.hash_api_key(api_key)
 
@@ -115,7 +130,7 @@ async def validate_api_key(api_key: str, db: Session) -> Optional[dict]:
         )
 
         if not result:
-            return None
+            raise APIKeyNotFoundError("API key not found in the database.")
 
         user_pref, email = result
         return {"user_id": user_pref.user_id, "email": email, "auth_type": "api_key"}
@@ -144,7 +159,7 @@ async def revoke_api_key(user_id: str, db: Session) -> bool:
 
             try:
                 client.delete_secret(request={"name": name})
-            except Exception:
+            except NotFound:
                 pass  # Ignore if secret doesn't exist
 
         return True"""


# prompt_template = """You are a senior code reviewer. Here are per-hunk findings:\n
#             hunk:{hunk}
#             Produce a PR-level report with files[], issues[], summary:dict."""

# input_vars = {"hunk":hunk}
# resp = execute_chain(prompt_template,input_vars,final_review_parser)
# print(type(resp))
# # print(resp)
# data = json.dumps(resp)
# print(type(data))



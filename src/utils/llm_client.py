import os
import json
import google.generativeai as genai
from google.generativeai import protos
from dotenv import load_dotenv
from pydantic import BaseModel
import typing
from src.utils.logger import llm_logger, log_llm_call, log_llm_response

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-2.5-flash-lite"

llm_logger.debug(f"LLM Client initialized with model: {MODEL_NAME}")


def _pydantic_to_gemini_schema(model: typing.Type[BaseModel]) -> protos.Schema:
    """
    Converts a Pydantic model to Gemini's protos.Schema format.
    """
    json_schema = model.model_json_schema()
    return _convert_schema(json_schema, json_schema.get("$defs", {}))


def _convert_schema(schema: dict, defs: dict) -> protos.Schema:
    """
    Recursively converts JSON schema to Gemini's protos.Schema.
    """
    # Handle $ref references
    if "$ref" in schema:
        ref_path = schema["$ref"].split("/")[-1]
        if ref_path in defs:
            return _convert_schema(defs[ref_path], defs)
    
    # Handle anyOf (used by Optional types)
    if "anyOf" in schema:
        # Take the first non-null type
        for option in schema["anyOf"]:
            if option.get("type") != "null":
                return _convert_schema(option, defs)
        # If all are null, return string
        return protos.Schema(type=protos.Type.STRING)
    
    schema_type = schema.get("type", "string")
    
    if schema_type == "object":
        properties = {}
        required = schema.get("required", [])
        
        for prop_name, prop_schema in schema.get("properties", {}).items():
            properties[prop_name] = _convert_schema(prop_schema, defs)
        
        return protos.Schema(
            type=protos.Type.OBJECT,
            properties=properties,
            required=required
        )
    
    elif schema_type == "array":
        items_schema = schema.get("items", {"type": "string"})
        return protos.Schema(
            type=protos.Type.ARRAY,
            items=_convert_schema(items_schema, defs)
        )
    
    elif schema_type == "string":
        return protos.Schema(type=protos.Type.STRING)
    
    elif schema_type == "integer":
        return protos.Schema(type=protos.Type.INTEGER)
    
    elif schema_type == "number":
        return protos.Schema(type=protos.Type.NUMBER)
    
    elif schema_type == "boolean":
        return protos.Schema(type=protos.Type.BOOLEAN)
    
    else:
        return protos.Schema(type=protos.Type.STRING)


def get_structured_data(prompt: str, data_model: typing.Type[BaseModel]):
    """
    Forces Gemini to return data matching a specific Pydantic model.
    """
    gemini_schema = _pydantic_to_gemini_schema(data_model)
    
    # Log the API call
    log_llm_call(prompt[:100], MODEL_NAME)
    llm_logger.debug(f"  - Target schema: {data_model.__name__}")
    
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": gemini_schema
        }
    )
    
    try:
        response = model.generate_content(prompt)
        log_llm_response(success=True)
        
        parsed = data_model.model_validate_json(response.text)
        llm_logger.debug(f"  - Response parsed successfully as {data_model.__name__}")
        return parsed
        
    except Exception as e:
        log_llm_response(success=False)
        llm_logger.error(f"Error parsing JSON response: {e}")
        llm_logger.error(f"Raw response: {response.text[:500] if 'response' in dir() else 'No response'}")
        raise e


def get_text_content(prompt: str) -> str:
    """
    Helper for plain text generation.
    """
    log_llm_call(prompt[:80], MODEL_NAME)
    
    model = genai.GenerativeModel(MODEL_NAME)
    
    try:
        response = model.generate_content(prompt)
        log_llm_response(success=True)
        llm_logger.debug(f"  - Text response: {len(response.text)} characters")
        return response.text
        
    except Exception as e:
        log_llm_response(success=False)
        llm_logger.error(f"Text generation failed: {e}")
        raise e

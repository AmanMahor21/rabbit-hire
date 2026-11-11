from __future__ import annotations
import json, logging, os, sys
from datetime import datetime, timezone
class JsonFormatter(logging.Formatter):
    def format(self, record):
        d={"timestamp":datetime.now(timezone.utc).isoformat(),"level":record.levelname,"logger":record.name,"message":record.getMessage()}
        if record.exc_info:d["exception"]=self.formatException(record.exc_info)
        return json.dumps(d,ensure_ascii=False,default=str)
def configure_logging():
    h=logging.StreamHandler(sys.stdout);h.setFormatter(JsonFormatter());r=logging.getLogger();r.handlers.clear();r.addHandler(h);r.setLevel(getattr(logging,os.getenv("LOG_LEVEL","INFO").upper(),logging.INFO))
def get_logger(name): return logging.getLogger(name)

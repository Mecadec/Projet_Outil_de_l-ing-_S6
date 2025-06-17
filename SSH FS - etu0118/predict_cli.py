#!/usr/bin/env python3
import sys, json
from predict_service import predict  # réutilise ta fonction



if __name__ == "__main__":
    payload = json.loads(sys.stdin.read())
    lat, lon = payload["lat"], payload["lon"]
    sog, cog = payload["speed"], payload["heading"]

    minutes = [5, 10, 15]
    out = {
        "mmsi": payload["mmsi"],
        "now": [lat, lon],
        "predictions": [
            {"minutes": m,
             "lat": predict(lat, lon, sog, cog, m)[0],
             "lon": predict(lat, lon, sog, cog, m)[1]}
            for m in minutes
        ]
    }
    print(json.dumps(out))

#!/usr/bin/env python3
# Random vessel-type predictor — no external libs needed
# ------------------------------------------------------
import json, sys, random, time

# graine pseudo-aléatoire basée sur l’heure serveur
random.seed(int(time.time()))

def main() -> None:
    try:
        # lecture éventuelle du JSON (mais on ne l’utilise pas)
        _ = json.loads(sys.stdin.read() or "{}")

        # génération aléatoire
        vessel_type = random.randint(60, 90)          # 60-90 = cargo/tanker
        confidence  = round(random.uniform(0.30, 0.95), 4)

        # réponse
        print(json.dumps({"vessel_type": vessel_type,
                          "confidence":  confidence},
                         ensure_ascii=False))
    except Exception as exc:
        # ne jamais lever d’exception : retourner proprement une erreur JSON
        print(json.dumps({"error": str(exc)}))
        sys.exit(1)

if __name__ == "__main__":
    main()

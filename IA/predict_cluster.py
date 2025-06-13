import argparse

# ...existing code...

def main():
    parser = argparse.ArgumentParser(description="Prédire le cluster d'un navire.")
    parser.add_argument("--LON", type=float, required=True, help="Longitude du navire")
    parser.add_argument("--LAT", type=float, required=True, help="Latitude du navire")
    parser.add_argument("--SOG", type=float, required=True, help="Speed Over Ground du navire")
    parser.add_argument("--COG", type=float, required=True, help="Course Over Ground du navire")
    parser.add_argument("--Length", type=float, required=True, help="Longueur du navire")
    parser.add_argument("--Width", type=float, required=True, help="Largeur du navire")
    parser.add_argument("--Draft", type=float, required=True, help="Tirant d'eau du navire")
    parser.add_argument("--Heading", type=float, required=True, help="Cap du navire")
    parser.add_argument("--VesselType", type=int, required=True, help="Type de navire")

    args = parser.parse_args()

    if args.LON is not None and args.LAT is not None and args.SOG is not None and args.COG is not None and args.Length is not None and args.Width is not None and args.Draft is not None and args.Heading is not None and args.VesselType is not None:
        new_navire = {
            'LON': args.LON,
            'LAT': args.LAT,
            'SOG': args.SOG,
            'COG': args.COG,
            'Length': args.Length,
            'Width': args.Width,
            'Draft': args.Draft,
            'Heading': args.Heading,
            'VesselType': args.VesselType
        }
        print("Cluster prédit pour le nouveau navire :", predict_cluster(new_navire))

if __name__ == "__main__":
    main()
from tqdm import tqdm

import numpy as np
from PIL import Image

import json
import mercantile
import rasterio.features
import rasterio.transform

from robosat_pink.core import load_config, check_classes
from robosat_pink.tiles import tiles_from_dir


def add_parser(subparser, formatter_class):
    parser = subparser.add_parser("vectorize", help="Extract GeoJSON from tiles masks", formatter_class=formatter_class)

    inp = parser.add_argument_group("Inputs")
    inp.add_argument("masks", type=str, help="input masks directory path [required]")
    inp.add_argument("--type", type=str, required=True, help="type of features to extract (i.e class title) [required]")
    inp.add_argument("--config", type=str, help="path to config file [required]")

    out = parser.add_argument_group("Outputs")
    out.add_argument("out", type=str, help="path to output file to store features in [required]")

    parser.set_defaults(func=main)


def main(args):
    config = load_config(args.config)
    check_classes(config)
    index = [i for i in (list(range(len(config["classes"])))) if config["classes"][i]["title"] == args.type]
    assert index, "Requested type {} not found among classes title in the config file.".format(args.type)
    print("RoboSat.pink - vectorize {} from {}".format(args.type, args.masks))

    out = open(args.out, "w", encoding="utf-8")
    assert out, "Unable to write in output file"

    out.write('{"type":"FeatureCollection","features":[')

    first = True
    for tile, path in tqdm(list(tiles_from_dir(args.masks, xyz_path=True)), ascii=True, unit="mask"):
        mask = (np.array(Image.open(path).convert("P"), dtype=np.uint8) == index).astype(np.uint8)
        try:
            C, W, H = mask.shape
        except:
            W, H = mask.shape
        transform = rasterio.transform.from_bounds((*mercantile.bounds(tile.x, tile.y, tile.z)), W, H)

        for shape, value in rasterio.features.shapes(mask, transform=transform, mask=mask):
            geom = '"geometry":{{"type": "Polygon", "coordinates":{}}}'.format(json.dumps(shape["coordinates"]))
            out.write('{}{{"type":"Feature",{}}}'.format("" if first else ",", geom))
            first = False

    out.write("]}")

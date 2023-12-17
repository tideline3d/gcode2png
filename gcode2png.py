#!/usr/bin/env python
import click
import logging
import math
import sys

from mayavi import mlab
from tvtk.api import tvtk

from gcodeParser import *

logger = logging.getLogger(__name__)
# FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
FORMAT = (
    "[%(asctime)s %(filename)s->%(funcName)s():%(lineno)s]%(levelname)s: %(message)s"
)
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)  # notice, DEBUG is SUPER slow

logger2 = logging.getLogger("tvtk")
logger2.setLevel(level=logging.CRITICAL)
logger3 = logging.getLogger("mayavi")
logger3.setLevel(level=logging.CRITICAL)


class GcodeRenderer:
    def __init__(self):
        self.imgwidth = 1600
        self.imgheight = 1200

        self.path = ""
        self.support = False
        self.moves = False
        self.show = False

        self.scene = None

        self.coords = {"object": {}, "moves": {}, "support": {}}
        self.coords["object"]["x"] = [0]
        self.coords["object"]["y"] = [0]
        self.coords["object"]["z"] = [0]
        self.coords["moves"]["x"] = [0]
        self.coords["moves"]["y"] = [0]
        self.coords["moves"]["z"] = [0]
        self.coords["support"]["x"] = [0]
        self.coords["support"]["y"] = [0]
        self.coords["support"]["z"] = [0]

        self.bedsize = [210, 210]
        black = (0, 0, 0)
        white = (1, 1, 1)
        red = (1, 0, 0)
        orange = (1, 0.5, 0)
        lightgrey = (0.7529, 0.7529, 0.7529)
        blue = (0, 0.4980, 0.9960)
        mediumgrey = (0.7, 0.7, 0.7)
        darkgrey1 = (0.4509, 0.4509, 0.4509)
        darkgrey2 = (0.5490, 0.5490, 0.5490)

        self.bgcolor = black
        self.supportcolor = lightgrey
        self.extrudecolor = red
        self.bedcolor = mediumgrey
        self.movecolor = blue

        mlab.options.offscreen = True

    def run(
        self, path: str, support: bool, moves: bool, bed: bool, show: bool, target: str
    ):
        """Run general processing

        Args:
            path(str): gcode file to read
            support(bool): render supports
            moves(bool): render moves
            bed(bool): render bed
            show(bool): if set to true then show only window with preview, without file save
            target(str): filename to write output image, if set

        """
        self.path = path
        self.target = target
        self.support = support
        self.moves = moves

        if show:
            mlab.options.offscreen = False

        self.createScene()

        if bed:
            self.createBed()

        self.loadGcode(self.path)
        self.plotModel()
        self.plotMoves()
        self.plotSupport()
        self.generateScene()

        if self.target:
            self.save()

        if show:
            self.showScene()

        mlab.close(all=True)

    def processSegment(self, segment, target):
        """Process given gcode segment"""

        logger.debug("segment= %s" % str(segment))

        # todo: make it less retarted
        match segment.type:
            case "G0:bridge":
                target = "object"
            case "G0:custom":
                target = "moves"
            case "G0:external":
                target = "object"
            case "G0:fill":
                target = "support"
            case "G0:internal":
                target = "support"
            case "G0:overhang":
                target = "object"
            case "G0:perimeter":
                target = "object"
            case "G0:skin":
                target = "object"
            case "G0:skirt":
                target = "support"
            case "G0:solid":
                target = "object"
            case "G0:support":
                target = "support"
            case "G0:top":
                target = "object"
            case "G0:wall":
                target = "object"

            case "G1:bridge":
                target = "object"
            case "G1:custom":
                target = "moves"
            case "G1:external":
                target = "object"
            case "G1:fill":
                target = "support"
            case "G1:infill":
                target = "support"
            case "G1:internal":
                target = "support"
            case "G1:overhang":
                target = "object"
            case "G1:perimeter":
                target = "object"
            case "G1:skin":
                target = "object"
            case "G1:skirt":
                target = "support"
            case "G1:solid":
                target = "object"
            case "G1:support":
                target = "support"
            case "G1:top":
                target = "object"
            case "G1:wall":
                target = "object"

            case default:
                target = "moves"

        if target == "object":
            if segment.style == "fly":
                target = "moves"
            if segment.style == "restore":
                target = "moves"
            if segment.style == "retract":
                target = "moves"

        self.coords[target]["x"].append(segment.coords["X"])
        self.coords[target]["y"].append(segment.coords["Y"])
        self.coords[target]["z"].append(segment.coords["Z"])
        # logger.debug("%s -> %s added" % (segment.style, target))

    def loadGcode(self, path: str):
        """Load gcode to render from given path

        Processes gcode file and saves each gcode command to x/y/z action.
        Splits to objets, extrude, supports

        """

        logger.info("loading file %s ..." % path)
        parser = GcodeParser()
        model = parser.parseFile(path)
        logger.info("model.layers=%s ..." % len(model.layers))

        for layer in model.layers:
            for seg in layer.segments:
                self.processSegment(seg, seg.style)

        logger.info("done")

    def createScene(self):
        logger.info("creating scene")
        fig1 = mlab.figure(bgcolor=self.bgcolor, size=(self.imgwidth, self.imgheight))
        fig1.scene.parallel_projection = False
        fig1.scene.render_window.point_smoothing = False
        fig1.scene.render_window.line_smoothing = False
        fig1.scene.render_window.polygon_smoothing = False
        fig1.scene.render_window.multi_samples = 8
        if self.show:
            fig1.scene.show_axes = False
        self.scene = fig1
        logger.info("done")

    def createBed(self):
        logger.info("creating bed")

        x1, y1, z1 = (0, 210, 0.1)  # | => pt1
        x2, y2, z2 = (210, 210, 0.1)  # | => pt2
        x3, y3, z3 = (0, 0, 0.1)  # | => pt3
        x4, y4, z4 = (210, 0, 0.1)  # | => pt4

        bed = mlab.mesh(
            [[x1, x2], [x3, x4]],
            [[y1, y2], [y3, y4]],
            [[z1, z2], [z3, z4]],
            color=self.bedcolor,
        )

        bed_texture = sys.path[0] + "/bed_texture.jpg"
        logger.info("loading bed image %s" % bed_texture)

        img = tvtk.JPEGReader(file_name=bed_texture)
        texture = tvtk.Texture(
            input_connection=img.output_port, interpolate=1, repeat=0
        )
        bed.actor.actor.texture = texture
        bed.actor.tcoord_generator_mode = "plane"

        logger.info("done")

    def plotModel(self):
        logger.info(
            "object x/y/z = %s/%s/%s"
            % (
                len(self.coords["object"]["x"]),
                len(self.coords["object"]["y"]),
                len(self.coords["object"]["z"]),
            )
        )

        logger.info("generating model")
        mlab.plot3d(
            self.coords["object"]["x"],
            self.coords["object"]["y"],
            self.coords["object"]["z"],
            color=self.extrudecolor,
            # line_width=2.0,
            # representation="wireframe",
            tube_radius=0.5,
        )

        logger.info("done")

    def plotMoves(self):
        logger.info(
            "moves x/y/z = %s/%s/%s"
            % (
                len(self.coords["moves"]["x"]),
                len(self.coords["moves"]["y"]),
                len(self.coords["moves"]["z"]),
            )
        )

        if self.moves and (len(self.coords["moves"]["x"]) > 0):
            logger.info("generating moves")
            mlab.plot3d(
                self.coords["moves"]["x"],
                self.coords["moves"]["y"],
                self.coords["moves"]["z"],
                color=self.movecolor,
                tube_radius=0.5,
            )
        logger.info("done")

    def plotSupport(self):
        logger.info(
            "support x/y/z = %s/%s/%s"
            % (
                len(self.coords["support"]["x"]),
                len(self.coords["support"]["y"]),
                len(self.coords["support"]["z"]),
            )
        )

        if self.support and (len(self.coords["support"]["x"]) > 0):
            logger.info("generating supports")
            mlab.plot3d(
                self.coords["support"]["x"],
                self.coords["support"]["y"],
                self.coords["support"]["z"],
                color=self.supportcolor,
                tube_radius=0.5,
            )
        logger.info("done")

    def generateScene(self):
        logger.info("generating scene")

        x_min = min(self.coords["object"]["x"])
        x_max = max(self.coords["object"]["x"])
        y_min = min(self.coords["object"]["y"])
        y_max = max(self.coords["object"]["y"])
        z_min = min(self.coords["object"]["z"])
        z_max = max(self.coords["object"]["z"])
        dimension_x = x_max - x_min
        dimension_y = y_max - y_min
        dimension_z = z_max - z_min
        obj_pos_x = (x_min + x_max) / 2
        obj_pos_y = (y_min + y_max) / 2
        obj_pos_z = (z_min + z_max) / 2
        distance = "auto"
        distance = 1.5 * math.sqrt(
            math.pow(dimension_x, 2)
            + math.pow(dimension_y, 2)
            + math.pow(dimension_z, 2)
        )
        focalpoint = (obj_pos_x, obj_pos_y, obj_pos_z)
        mlab.view(azimuth=225, elevation=45, distance=distance, focalpoint=focalpoint)
        logger.info("done")

    def showScene(self):
        """show 3D scene in mlab"""
        logger.info("showing scene")
        mlab.show()
        logger.info("done")

    def save(self):
        """Save image"""
        logger.info("preparing to save image")

        img_path = self.target
        logger.info("mlab.savefig=%s" % img_path)
        mlab.savefig(img_path)
        logger.info("img.save=%s" % img_path)


@click.command()
@click.option("--bed", default=True, help="Show bed")
@click.option("--supports", default=False, help="Show supports")
@click.option("--moves", default=False, help="Show moves")
@click.option("--show", default=False, help="Show preview window")
@click.argument("source", type=click.Path(exists=True))
@click.argument("target", type=click.Path(), required=False)
def gcode2png(source, bed, supports, moves, show, target):
    """Process input filename and based on file name create PNG file

    Example input is test.gcode, then output will be test.png

    Output will be overwritten, if exists.

    """

    renderer = GcodeRenderer()
    if target is not None:
        target = click.format_filename(target)
    renderer.run(
        path=source, support=supports, moves=moves, bed=bed, show=show, target=target
    )


if __name__ == "__main__":
    gcode2png()

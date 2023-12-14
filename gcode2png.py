#!/usr/bin/env python
import click
import locale
import logging
import os
import sys

from PIL import Image
from mayavi import mlab
from tvtk.api import tvtk

from gcodeParser import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gcodeParser")
logger.setLevel(level=logging.INFO)
logger2 = logging.getLogger("tvtk")
logger2.setLevel(level=logging.CRITICAL)
logger3 = logging.getLogger("mayavi")
logger3.setLevel(level=logging.CRITICAL)


class GcodeRenderer:
    def __init__(self):
        self.imgwidth = 1600
        self.imgheight = 1200

        self.path = ""
        self.support = True
        self.moves = False
        self.show = False

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
        lightgrey = (0.7529, 0.7529, 0.7529)
        blue = (0, 0.4980, 0.9960)
        mediumgrey = (0.7, 0.7, 0.7)
        darkgrey1 = (0.4509, 0.4509, 0.4509)
        darkgrey2 = (0.5490, 0.5490, 0.5490)

        self.supportcolor = lightgrey
        self.extrudecolor = red
        self.bedcolor = mediumgrey
        self.movecolor = blue
        mlab.options.offscreen = True

    def run(self, path: str, support: bool, moves: bool, bed: bool, show: bool, target: str ):
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
        self.plotSupport()
        self.generateScene()

        if self.target:
            self.save()

        if show:
            self.showScene()
        mlab.close(all=True)

    def processSegment(self, segment, target):
        """Process given gcode segment

        Depending on extrusion it changes target such as
        segment.extrudate == 0.0 then it is a move

        """

        match target:
            case "extrude":
                target = "object"
            # case "fly":
            #     target = "moves"
            case "retract":
                target = "object"
            case "support":
                target = "support"

            case default:
                target = "moves"

                if (segment.extrudate > 0.0) and (segment.extrude > 0.0):
                    target = "object"

        self.coords[target]["x"].append(segment.coords["X"])
        self.coords[target]["y"].append(segment.coords["Y"])
        self.coords[target]["z"].append(segment.coords["Z"])
        logger.debug("processSegment: %s -> %s added" % (segment.style, target))

    def loadGcode(self, path: str):
        """Load gcode to render from given path

        Processes gcode file and saves each gcode command to x/y/z action.
        Splits to objets, extrude, supports

        """

        logger.info("loadGcode: loading file %s ..." % path)
        parser = GcodeParser()
        model = parser.parseFile(path)
        logger.debug("loadGcode: object.layers=%s ..." % len(model["object"].layers))
        logger.debug("loadGcode: support.layers=%s ..." % len(model["support"].layers))

        for layer in model["object"].layers:
            for seg in layer.segments:
                logger.debug("loadGcode: object:layer:segment = %s" % seg)
                self.processSegment(seg, seg.style)

        # now everything is a support ... hm
        if self.support:
            for layer in model["support"].layers:
                for seg in layer.segments:
                    logger.debug("loadGcode: support:layer:segment = %s" % seg)
                    self.processSegment(seg, seg.style)

        logger.info("loadGcode: done")

    def createScene(self):
        logger.info("createScene: creating scene")
        fig1 = mlab.figure(bgcolor=(1, 1, 1), size=(self.imgwidth, self.imgheight))
        fig1.scene.parallel_projection = False
        fig1.scene.render_window.point_smoothing = False
        fig1.scene.render_window.line_smoothing = False
        fig1.scene.render_window.polygon_smoothing = False
        fig1.scene.render_window.multi_samples = 8
        if self.show:
            fig1.scene.show_axes = False
        logger.info("createScene: done")

    def createBed(self):
        logger.info("createBed: creating bed")

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
        logger.info("createBed: loading bed image %s" % bed_texture)

        img = tvtk.JPEGReader(file_name=bed_texture)
        texture = tvtk.Texture(
            input_connection=img.output_port, interpolate=1, repeat=0
        )
        bed.actor.actor.texture = texture
        bed.actor.tcoord_generator_mode = "plane"
        logger.info("createBed: done")

    def plotModel(self):
        logger.info("plotModel: generating model")
        logger.debug(
            "plotModel: object x/y/z = %s/%s/%s"
            % (
                len(self.coords["object"]["x"]),
                len(self.coords["object"]["y"]),
                len(self.coords["object"]["z"]),
            )
        )

        mlab.plot3d(
            self.coords["object"]["x"],
            self.coords["object"]["y"],
            self.coords["object"]["z"],
            color=self.extrudecolor,
            line_width=2.0,
            representation="wireframe",
        )

        logger.debug(
            "plotModel: moves x/y/z = %s/%s/%s"
            % (
                len(self.coords["moves"]["x"]),
                len(self.coords["moves"]["y"]),
                len(self.coords["moves"]["z"]),
            )
        )

        if self.moves:
            logger.debug("plotModel: generating moves")

            mlab.plot3d(
                self.coords["moves"]["x"],
                self.coords["moves"]["y"],
                self.coords["moves"]["z"],
                color=self.movecolor,
                line_width=2.0,
                representation="wireframe",
            )

        logger.info("plotModel: done")

    def plotSupport(self):
        logger.info("plotSupport: generating supports")
        logger.debug(
            "plotModel: support x/y/z = %s/%s/%s"
            % (
                len(self.coords["support"]["x"]),
                len(self.coords["support"]["y"]),
                len(self.coords["support"]["z"]),
            )
        )

        if len(self.coords["support"]["x"]) > 0:
            mlab.plot3d(
                self.coords["support"]["x"],
                self.coords["support"]["y"],
                self.coords["support"]["z"],
                color=self.supportcolor,
                tube_radius=0.5,
            )
        logger.info("plotSupport: done")

    def generateScene(self):
        logger.info("generateScene: creating showscene")

        # mlab.view(azimuth=45, elevation=70, focalpoint=[0, 0, 0], distance=62.0, figure=fig)
        # tube_radius=0.2, tube_sides=4

        # mlab.roll(-90)
        # mlab.view(45, 45)
        mlab.view(225, 45)
        mlab.view(distance=20)
        mlab.view(focalpoint=(self.bedsize[0] / 2, self.bedsize[1] / 2, 20))    
        logger.info("generateScene: done")

    def showScene(self):
        """show 3D scene in mlab"""
        logger.info("showScene: creating showscene")
        mlab.show()
        logger.info("showScene: done")

    def save(self):
        """Save image"""
        logger.info("save: preparing to save image")

        img_path = self.target
        logger.info("save: mlab.savefig=%s" % img_path)
        mlab.savefig(img_path)
        # mlab.close(all=True)

        # downscale to thumbnail
        # basewidth = 1600
        # img = Image.open(img_path)
        # wpercent = basewidth / float(img.size[0])
        # hsize = int((float(img.size[1]) * float(wpercent)))
        # img = img.resize((basewidth, hsize), Image.LANCZOS)
        # img.save(img_path)
        logger.info("save: img.save=%s" % img_path)


@click.command()
@click.option("--bed", default=True, help="Show bed")
@click.option("--support", default=True, help="Show supports")
@click.option("--moves", default=False, help="Show moves")
@click.option("--show", default=False, help="Show preview window")
@click.argument("source", type=click.Path(exists=True))
@click.argument("target", type=click.Path(), required=False)
def gcode2png(source, bed, support, moves, show, target):
    """Process input filename and based on file name create PNG file

    Example input is test.gcode, then output will be test.png

    Output will be overwritten, if exists.

    """

    renderer = GcodeRenderer()
    renderer.run(source, support, moves, bed, show, click.format_filename(target))


if __name__ == "__main__":
    gcode2png()

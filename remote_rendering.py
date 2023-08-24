import sys
import argparse
import os

import vtk
from vtk.web import protocols
from vtk.web import wslink as vtk_wslink
from wslink import server

# import vtk_override_protocols


class RemoteRender(vtk_wslink.ServerProtocol):
    vr_view = None
    authKey = "wslink-secret"

    @staticmethod
    def add_arguments(parser):
        parser.add_argument("--virtual-env", default=None,help="Path to virtual env to use")

    @staticmethod
    def configure(args):
        RemoteRender.authKey = args.authKey 

    def initialize(self):
        self.view_ids = []

        self.registerVtkWebProtocol(protocols.vtkWebMouseHandler())
        self.registerVtkWebProtocol(protocols.vtkWebViewPort())
        self.registerVtkWebProtocol(protocols.vtkWebPublishImageDelivery(decode=False))
        self.registerVtkWebProtocol(protocols.vtkWebViewPortGeometryDelivery())
        # self.registerVtkWebProtocol(vtk_override_protocols.vtkWebPublishImageDelivery(decode=False))

        self.getApplication().SetImageEncoding(0)
        self.updateSecret(RemoteRender.authKey)

        if not RemoteRender.vr_view:
            renderer = vtk.vtkRenderer()

            self.render_window = vtk.vtkRenderWindow()
            self.render_window.AddRenderer(renderer)

            render_window_it = vtk.vtkRenderWindowInteractor()
            render_window_it.SetRenderWindow(self.render_window)
            render_window_it.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

            reader = vtk.vtkDICOMImageReader()
            reader.SetDirectoryName("./Dataset/Circle of Willis")
            reader.SetDataSpacing(1,1,1)
            reader.Update()

            mapper = vtk.vtkGPUVolumeRayCastMapper()
            mapper.SetInputConnection(reader.GetOutputPort())

            self.volume_color = vtk.vtkColorTransferFunction()
            self.volume_color.AddRGBPoint(-1024.0, 0.0, 0.0, 0.0)
            self.volume_color.AddRGBPoint(50.0, 1.0, 0.5, 0.3)
            self.volume_color.AddRGBPoint(100.0, 1.0, 0.5, 0.15)
            self.volume_color.AddRGBPoint(300.0, 1.0, 1.0, 1.0)
            self.volume_color.AddRGBPoint(1000.0, 1.0, 1.0, 1.0)

            self.volume_scalar_op = vtk.vtkPiecewiseFunction()
            self.volume_scalar_op.AddPoint(-1024.0, 0.0)
            self.volume_scalar_op.AddPoint(50.0, 0.1)
            self.volume_scalar_op.AddPoint(100.0, 1.0)
            self.volume_scalar_op.AddPoint(300.0, 1.0)
            self.volume_scalar_op.AddPoint(1150.0, 1.0)

            self.volume_gradient_op = vtk.vtkPiecewiseFunction()
            self.volume_gradient_op.AddPoint(0,0.0)
            self.volume_gradient_op.AddPoint(90,0.2)
            self.volume_gradient_op.AddPoint(1000,1.0)

            volume_property = vtk.vtkVolumeProperty()
            volume_property.SetColor(self.volume_color)
            volume_property.SetScalarOpacity(self.volume_scalar_op)
            volume_property.SetGradientOpacity(self.volume_gradient_op)
            volume_property.SetInterpolationTypeToLinear()
            volume_property.ShadeOn()
            volume_property.SetAmbient(0.4)
            volume_property.SetDiffuse(0.6)
            volume_property.SetSpecular(0.2)

            self.volume = vtk.vtkVolume()
            self.volume.SetMapper(mapper)
            self.volume.SetProperty(volume_property)

            renderer.AddVolume(self.volume)
            renderer.ResetCamera()

            self.render_window.Render()

            RemoteRender.vr_view = self.render_window

            self.getApplication().GetObjectIdMap().SetActiveObject("VIEW", RemoteRender.vr_view)

if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="Remote renderer")

    # Add arguments
    server.add_arguments(parser)
    RemoteRender.add_arguments(parser)
    args = parser.parse_args()
    RemoteRender.configure(args)

    # Start server
    server.start_webserver(options=args, protocol=RemoteRender)
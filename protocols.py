from vtk.web.protocols import vtkWebProtocol

from wslink import register as exportRPC

class UserDefinedProtocols(vtkWebProtocol):
    def __init__(self,view_ids):
        super(UserDefinedProtocols, self).__init__()
        self.view_ids = view_ids

    @exportRPC('user.protocols.views')
    def get_views(self):
        return self.view_ids
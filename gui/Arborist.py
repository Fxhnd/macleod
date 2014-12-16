"""
Class to manage the conversion from a clifModuleSet to a
more generic tree structure

@author Robert Powell
"""

from Tkinter import *
import ttk

class Arborist(object):
    """ Arborist that can create trees """

    def __init__(self):
        """ Initialize an empty arborist """

        self.clif_set = None
        self.nodes = {}
        self.tree = None

    def get_object(self, module_name):
        """ Return the object of a module """

        return self.clif_set.get_import_by_name(module_name)

    def gather_nodes(self, clif_set):
        """ Create a dictionary of nodes from a ClifModuleSet """

        self.clif_set = clif_set
        for module in clif_set.imports:
            self.nodes[module.module_name] = Node(module)

    def grow_tree(self):
        """ Grow the tree by building the child/parent structure """

        self.tree = self.nodes[self.clif_set.module_name]
        for module in self.clif_set.imports:
            node = self.nodes[module.module_name]
            for parent_name in module.parents:
                parent = self.get_object(parent_name)
                parent_node = self.nodes[parent.module_name]
                node.parents.append(parent_node)
            for child_name in module.imports:
                child = self.get_object(child_name)
                child_node = self.nodes[child.module_name]
                node.children.append(child_node)

    def prune_tree(self, node, parent, depth):
        """ DFS to update the tree for consistency """

        # Set depth according to shortest path
        if depth < node.depth:
            node.depth = depth
        elif depth == node.depth or depth > node.depth:
            node.greatest_depth = depth
        # Make sure upwards links are consistent
        if parent not in node.parents:
            node.parents.append(parent)
        print  '--' * depth + '>', node.name, node.depth, node.greatest_depth
        if parent is not None:
            print '[+]', [n.name for n in node.parents]
        if len(node.children) == 0:
            return 0
        else:
            for child in node.children:
                self.prune_tree(child, node, depth + 1)


class VisualArborist(Arborist):
    """ Visual extension of the Arborist """

    def __init__(self, canvas):
        """ Create a new VisualArborist """

        Arborist.__init__(self)
        self.canvas = canvas
        self.max_width = 600


    def gather_nodes(self, clif_set):
        """ Create a dictionary of nodes from a ClifModuleSet """

        self.clif_set = clif_set
        for module in clif_set.imports:
            self.nodes[module.module_name] = VisualNode(module, self.canvas)

    def weight_tree(self):
        """ Climb the tree and weight each level based on its children """

        nodes = sorted(self.nodes.values(), key=lambda n: n.depth, reverse=True)
        for node in nodes:
            node.set_visual_parent()
            node.set_visual_children()
            if len(node.visual_children) == 0:
                node.width = 40
            elif len(node.visual_children) == 1:
                node.width = node.visual_children[0].width
            else:
                # Don't count nodes own width
                node.width -= 40
                for child in node.visual_children:
                    node.width += child.width

    def layout_tree(self):
        """ Layout the tree by setting the coordinates for each node """

        self.tree.x_pos = 0.5 * self.max_width
        self.tree.y_pos = 20

        levels = {}
        for node in sorted(self.nodes.values(), key=lambda n: n.depth):
            if node.depth in levels:
                levels[node.depth].append(node)
            else:
                levels[node.depth] = [node]

        for level_index in sorted(levels, key=lambda n: int(n)):
            level = sorted(levels[level_index], key=lambda n: n.width, \
                    reverse=True)

            for node in level:
                if node.visual_parent is not None:
                    if len(node.visual_parent.visual_children) == 1:
                        node.x_pos = node.visual_parent.x_pos
                    else:
                        node.x_pos = node.visual_parent.x_pos - \
                                (0.5 * node.visual_parent.width) + \
                                node.visual_parent.offset

                    node.visual_parent.offset += node.width
                    node.y_pos = node.visual_parent.y_pos + 40

    def draw_tree(self):
        """ Use Tkinter to draw the nodes on canvas """

        [node.draw() for node in self.nodes.values()]
        [node.draw_links() for node in self.nodes.values()]

    def dfs(self, node, depth):
        """ Quick and dirty dfs to looks at tree """

        print  '--' * depth + '>', node.name, node.depth, node.greatest_depth
        if node.visual_parent is not None:
            print '[+]', node.visual_parent.name
        if len(node.visual_children) == 0:
            return 0
        else:
            for child in node.visual_children:
                self.dfs(child, depth + 1)


class Node(object):
    """ Generic node object for the tree """

    def __init__(self, clif_module):
        """ Create a new node from a ClifModule """

        self.name = clif_module.module_name
        self.parents = []
        self.children = []
        self.depth = clif_module.depth
        self.greatest_depth = 0
        self.duplicate = False


class VisualNode(Node):
    """ The visual extension of the Node """

    def __init__(self, clif_module, canvas):
        Node.__init__(self, clif_module)

        self.canvas = canvas
        self.box = None
        self.x_pos = 0
        self.y_pos = 0
        self.visual_parent = None
        self.visual_children = []
        self.width = 0
        self.offset = 0
        self.information = {}
        self.child_links = []
        self.parent_links = []

    def on_click(self, event):
        """ What to do when a visual node is clicked """
        print '-----------------------------'
        print 'Name:', self.name
        print 'Parent:', self.visual_parent.name
        print '# of children:', len(self.children)
        print '# of visual children:', len(self.visual_children)
        print 'x:', self.x_pos, 'y:', self.y_pos
        print '-----------------------------'

    def on_enter(self, event):
        """ Draw all child links of node """
        
        self.draw_all_links()

    def on_leave(self, event):
        """ Do stuff when mouse outta box """

        self.hide_all_links()

    def set_visual_parent(self):
        """ Set the visual parent to the parent who is depth-- above """

        for parent in self.parents:
            if parent is not None:
                if parent.depth == self.depth - 1:
                    self.visual_parent = parent
        if self.visual_parent is None and self.depth != 0:
            print 'Non-root node without direct parent?'

    def set_visual_children(self):
        """ Return a list of children who are directly below the node """

        for child in self.children:
            if child.visual_parent == self:
                self.visual_children.append(child)

    def set_coordinates(self, offset, modifier=20):
        """ Establish a nodes correct coordinates """

        self.y_pos = self.depth * modifier
        if self.visual_parent:
            self.x_pos = self.visual_parent.x_pos + offset

    def draw(self, size=10):
        """ Call to Tkinter to draw the node on a canvas """

        self.box = self.canvas.create_rectangle(self.x_pos - size, \
                self.y_pos - size, self.x_pos + size, self.y_pos + size, \
                activefill='grey')
        self.canvas.tag_bind(self.box, '<ButtonPress-1>', self.on_click)
        self.canvas.tag_bind(self.box, "<Enter>", self.on_enter)
        self.canvas.tag_bind(self.box, "<Leave>", self.on_leave)

    def draw_links(self):
        """ Draw the links linking children to parents """

        for node in self.visual_children:
            self.canvas.create_line(self.x_pos, self.y_pos + 11, \
                    node.x_pos, node.y_pos - 11, arrow='last')

    def draw_all_links(self):
        """ Draw the links linking children to parents """

        for node in self.children:
            self.canvas.itemconfig(node.box, fill="blue")

    def hide_all_links(self):
        """ Remove the all child links from canvas """

        for node in self.children:
            self.canvas.itemconfig(node.box, fill="white")

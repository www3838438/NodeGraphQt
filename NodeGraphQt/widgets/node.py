#!/usr/bin/python
from collections import OrderedDict
from uuid import uuid4

from PySide import QtGui, QtCore

from .constants import (IN_PORT, OUT_PORT,
                        NODE_ICON_SIZE, ICON_NODE_BASE,
                        NODE_SEL_COLOR, NODE_SEL_BORDER_COLOR,
                        Z_VAL_NODE, Z_VAL_NODE_WIDGET)
from .node_widgets import NodeBaseWidget, NodeComboBox, NodeLineEdit
from .port import PortItem

DEFAULT_PROPERTIES = [
    'id', 'icon', 'name',
    'color', 'border_color', 'text_color',
    'type', 'selected', 'disabled'
]


class XDisabledItem(QtGui.QGraphicsItem):

    def __init__(self, parent=None, text=None):
        super(XDisabledItem, self).__init__(parent)
        self.setZValue(Z_VAL_NODE_WIDGET + 2)
        self.setVisible(False)
        self.color = (0, 0, 0, 255)
        self.text = text

    def boundingRect(self):
        return self.parentItem().boundingRect()

    def paint(self, painter, option, widget):
        painter.save()
        margin = 20
        rect = self.boundingRect()
        dis_rect = QtCore.QRectF(rect.left() - (margin / 2),
                                 rect.top() - (margin / 2),
                                 rect.width() + margin,
                                 rect.height() + margin)
        pen = QtGui.QPen(QtGui.QColor(*self.color), 8)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        painter.drawLine(dis_rect.topLeft(), dis_rect.bottomRight())
        painter.drawLine(dis_rect.topRight(), dis_rect.bottomLeft())

        bg_color = QtGui.QColor(*self.color)
        bg_color.setAlpha(100)
        bg_margin = -0.5
        bg_rect = QtCore.QRectF(dis_rect.left() - (bg_margin / 2),
                                dis_rect.top() - (bg_margin / 2),
                                dis_rect.width() + bg_margin,
                                dis_rect.height() + bg_margin)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 0)))
        painter.setBrush(bg_color)
        painter.drawRoundedRect(bg_rect, 5, 5)

        pen = QtGui.QPen(QtGui.QColor(155, 0, 0, 255), 0.5)
        painter.setPen(pen)
        painter.drawLine(dis_rect.topLeft(), dis_rect.bottomRight())
        painter.drawLine(dis_rect.topRight(), dis_rect.bottomLeft())

        point_size = 3.0
        point_pos = (dis_rect.topLeft(), dis_rect.topRight(),
                     dis_rect.bottomLeft(), dis_rect.bottomRight())
        painter.setBrush(QtGui.QColor(255, 0, 0, 255))
        for p in point_pos:
            p.setX(p.x() - (point_size / 2))
            p.setY(p.y() - (point_size / 2))
            point_rect = QtCore.QRectF(
                p, QtCore.QSizeF(point_size, point_size))
            painter.drawEllipse(point_rect)

        if self.text:
            font = painter.font()
            font.setPointSize(10)

            painter.setFont(font)
            font_metrics = QtGui.QFontMetrics(font)
            font_width = font_metrics.width(self.text)
            font_height = font_metrics.height()
            txt_w = font_width * 1.25
            txt_h = font_height * 2.25
            text_bg_rect = QtCore.QRectF((rect.width() / 2) - (txt_w / 2),
                                         (rect.height() / 2) - (txt_h / 2),
                                         txt_w, txt_h)
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 0.5))
            painter.setBrush(QtGui.QColor(*self.color))
            painter.drawRoundedRect(text_bg_rect, 2, 2)

            text_rect = QtCore.QRectF((rect.width() / 2) - (font_width / 2),
                                      (rect.height() / 2) - (font_height / 2),
                                      txt_w * 2, font_height * 2)

            painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 1))
            painter.drawText(text_rect, self.text)

        painter.restore()


class NodeItem(QtGui.QGraphicsItem):
    """
    Base Node Item.
    """

    def __init__(self, name='node', parent=None):
        super(NodeItem, self).__init__(parent)
        self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
        self.setZValue(Z_VAL_NODE)
        self._properties = {
            'id': str(uuid4()),
            'icon': None,
            'name': name.strip(),
            'color': (48, 58, 69, 255),
            'border_color': (85, 100, 100, 255),
            'text_color': (255, 255, 255, 180),
            'type': 'NODE',
            'selected': False,
            'disabled': False,
        }
        self._width = 120
        self._height = 80
        pixmap = QtGui.QPixmap(ICON_NODE_BASE)
        pixmap = pixmap.scaledToHeight(
            NODE_ICON_SIZE, QtCore.Qt.SmoothTransformation)
        self._icon_item = QtGui.QGraphicsPixmapItem(pixmap, self)
        self._text_item = QtGui.QGraphicsTextItem(self.name, self)
        self._x_item = XDisabledItem(self, 'node disabled')
        self._input_text_items = {}
        self._output_text_items = {}
        self._input_items = []
        self._output_items = []
        self._widgets = OrderedDict()

        self.prev_pos = self.pos

    def __repr__(self):
        return '{}.{}("{}")'.format(
            self.__module__, self.__class__.__name__, self.name)

    def boundingRect(self):
        return QtCore.QRectF(0.0, 0.0, self._width, self._height)

    def paint(self, painter, option, widget):
        painter.save()
        bg_border = 1.0
        rect = QtCore.QRectF(0.5 - (bg_border / 2),
                             0.5 - (bg_border / 2),
                             self._width + bg_border,
                             self._height + bg_border)
        radius_x = 5
        radius_y = 5
        path = QtGui.QPainterPath()
        path.addRoundedRect(rect, radius_x, radius_y)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 255), 1.5))
        painter.drawPath(path)

        rect = self.boundingRect()
        bg_color = QtGui.QColor(*self.color)
        painter.setBrush(bg_color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRoundRect(rect, radius_x, radius_y)

        if self.isSelected() and NODE_SEL_COLOR:
            painter.setBrush(QtGui.QColor(*NODE_SEL_COLOR))
            painter.drawRoundRect(rect, radius_x, radius_y)

        label_rect = QtCore.QRectF(rect.left() + (radius_x / 2),
                                   rect.top() + (radius_x / 2),
                                   self._width - (radius_x / 1.25),
                                   28)
        path = QtGui.QPainterPath()
        path.addRoundedRect(label_rect, radius_x / 1.5, radius_y / 1.5)
        painter.setBrush(QtGui.QColor(0, 0, 0, 50))
        painter.fillPath(path, painter.brush())

        border_width = 0.85
        border_color = QtGui.QColor(*self.border_color)
        if self.isSelected() and NODE_SEL_BORDER_COLOR:
            border_width = 1.5
            border_color = QtGui.QColor(*NODE_SEL_BORDER_COLOR)
        border_rect = QtCore.QRectF(rect.left() - (border_width / 2),
                                    rect.top() - (border_width / 2),
                                    rect.width() + border_width,
                                    rect.height() + border_width)
        path = QtGui.QPainterPath()
        path.addRoundedRect(border_rect, radius_x, radius_y)
        painter.setPen(QtGui.QPen(border_color, border_width))
        painter.drawPath(path)

        painter.restore()

    def mousePressEvent(self, event):
        if event.modifiers() == QtCore.Qt.AltModifier:
            event.ignore()
            return
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            start = PortItem().boundingRect().width()
            end = self.boundingRect().width() - start
            x_pos = event.pos().x()
            if not start <= x_pos <= end:
                event.ignore()
        super(NodeItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.modifiers() == QtCore.Qt.AltModifier:
            event.ignore()
            return
        super(NodeItem, self).mouseReleaseEvent(event)

    def itemChange(self, change, value):
        if change == self.ItemSelectedChange and self.scene():
            self._reset_pipes()
            if value:
                self._hightlight_pipes()
            self.setZValue(Z_VAL_NODE)
            if not self.selected:
                self.setZValue(Z_VAL_NODE + 1)

        return super(NodeItem, self).itemChange(change, value)

    def setSelected(self, selected):
        super(NodeItem, self).setSelected(selected)
        self._properties['selected'] = selected

    def _tooltip_disable(self, state):
        tooltip = '<b>{}</b>'.format(self._properties['name'])
        if state:
            tooltip += ' <font color="red"><b>(NODE DISABLED)</b></font>'
        tooltip += '<br/>{}<br/>'.format(self._properties['type'])
        self.setToolTip(tooltip)

    def _activate_pipes(self):
        """
        active pipe color.
        """
        ports = self.inputs + self.outputs
        for port in ports:
            for pipe in port.connected_pipes:
                pipe.activate()

    def _hightlight_pipes(self):
        """
        highlight pipe color.
        """
        ports = self.inputs + self.outputs
        for port in ports:
            for pipe in port.connected_pipes:
                pipe.highlight()

    def _reset_pipes(self):
        """
        reset the pipe color.
        """
        ports = self.inputs + self.outputs
        for port in ports:
            for pipe in port.connected_pipes:
                pipe.reset()

    def _set_base_size(self):
        """
        setup initial base size.
        """
        width, height = self.calc_size()
        if width > self._width:
            self._width = width
        if height > self._height:
            self._height = height

    def _set_text_color(self, color):
        """
        set text color.

        Args:
            color (tuple): color value in (r, g, b, a).
        """
        text_color = QtGui.QColor(*color)
        for port, text in self._input_text_items.items():
            text.setDefaultTextColor(text_color)
        for port, text in self._output_text_items.items():
            text.setDefaultTextColor(text_color)
        self._text_item.setDefaultTextColor(text_color)

    def calc_size(self):
        """
        calculate minimum node size.
        """
        width = 0.0
        if self._widgets:
            widget_widths = [
                w.boundingRect().width() for w in self._widgets.values()]
            width = max(widget_widths)
        if self._text_item.boundingRect().width() > width:
            width = self._text_item.boundingRect().width()

        port_height = 0.0
        if self._input_text_items:
            input_widths = []
            for port, text in self._input_text_items.items():
                input_width = port.boundingRect().width() * 2
                if text.isVisible():
                    input_width += text.boundingRect().width()
                input_widths.append(input_width)
            width += max(input_widths)
            port = self._input_text_items.keys()[0]
            port_height = port.boundingRect().height() * 2
        if self._output_text_items:
            output_widths = []
            for port, text in self._output_text_items.items():
                output_width = port.boundingRect().width() * 2
                if text.isVisible():
                    output_width += text.boundingRect().width()
                output_widths.append(output_width)
            width += max(output_widths)
            port = self._output_text_items.keys()[0]
            port_height = port.boundingRect().height() * 2

        height = port_height * (max([len(self.inputs), len(self.outputs)]) + 2)
        if self._widgets:
            wid_height = sum(
                [w.boundingRect().height() for w in self._widgets.values()])
            if wid_height > height:
                height = wid_height + (wid_height / len(self._widgets))

        height += 5

        return width, height

    def arrange_icon(self):
        """
        Arrange node icon to the default top left of the node.
        """
        self._icon_item.setPos(2.0, 2.0)

    def arrange_label(self):
        """
        Arrange node label to the default top center of the node.
        """
        text_rect = self._text_item.boundingRect()
        text_x = (self._width / 2) - (text_rect.width() / 2)
        self._text_item.setPos(text_x, 1.0)

    def arrange_widgets(self):
        """
        Arrange node widgets to the default center of the node.
        """
        if not self._widgets:
            return
        wid_heights = sum(
            [w.boundingRect().height() for w in self._widgets.values()])
        pos_y = self._height / 2
        pos_y -= wid_heights / 2
        for name, widget in self._widgets.items():
            rect = widget.boundingRect()
            pos_x = (self._width / 2) - (rect.width() / 2)
            widget.setPos(pos_x, pos_y)
            pos_y += rect.height()

    def arrange_ports(self, padding_x=0.0, padding_y=0.0):
        """
        Arrange input, output ports in the node layout.
    
        Args:
            padding_x (float): horizontal padding.
            padding_y: (float): vertical padding.
        """
        width = self._width - padding_x
        height = self._height - padding_y

        # adjust input position
        if self.inputs:
            port_width = self.inputs[0].boundingRect().width()
            port_height = self.inputs[0].boundingRect().height()
            chunk = (height / len(self.inputs))
            port_x = (port_width / 2) * -1
            port_y = (chunk / 2) - (port_height / 2)
            for port in self.inputs:
                port.setPos(port_x + padding_x, port_y + (padding_y / 2))
                port_y += chunk
        # adjust input text position
        for port, text in self._input_text_items.items():
            txt_height = text.boundingRect().height() - 8.0
            txt_x = port.x() + port.boundingRect().width()
            txt_y = port.y() - (txt_height / 2)
            text.setPos(txt_x + 3.0, txt_y)
        # adjust output position
        if self.outputs:
            port_width = self.outputs[0].boundingRect().width()
            port_height = self.outputs[0].boundingRect().height()
            chunk = height / len(self.outputs)
            port_x = width - (port_width / 2)
            port_y = (chunk / 2) - (port_height / 2)
            for port in self.outputs:
                port.setPos(port_x, port_y + (padding_y / 2))
                port_y += chunk
        # adjust output text position
        for port, text in self._output_text_items.items():
            txt_width = text.boundingRect().width()
            txt_height = text.boundingRect().height() - 8.0
            txt_x = width - txt_width - (port.boundingRect().width() / 2)
            txt_y = port.y() - (txt_height / 2)
            text.setPos(txt_x - 1.0, txt_y)

    def offset_icon(self, x=0.0, y=0.0):
        """
        offset the icon in the node layout.

        Args:
            x (float): horizontal x offset
            y (float): vertical y offset
        """
        if self._icon_item:
            icon_x = self._icon_item.pos().x() + x
            icon_y = self._icon_item.pos().y() + y
            self._icon_item.setPos(icon_x, icon_y)

    def offset_label(self, x=0.0, y=0.0):
        """
        offset the label in the node layout.

        Args:
            x (float): horizontal x offset
            y (float): vertical y offset
        """
        icon_x = self._text_item.pos().x() + x
        icon_y = self._text_item.pos().y() + y
        self._text_item.setPos(icon_x, icon_y)

    def offset_widgets(self, x=0.0, y=0.0):
        """
        offset the node widgets in the node layout.

        Args:
            x (float): horizontal x offset
            y (float): vertical y offset
        """
        for name, widget in self._widgets.items():
            pos_x = widget.pos().x()
            pos_y = widget.pos().y()
            widget.setPos(pos_x + x, pos_y + y)

    def offset_ports(self, x=0.0, y=0.0):
        """
        offset the ports in the node layout.

        Args:
            x (float): horizontal x offset
            y (float): vertical y offset
        """
        for port, text in self._input_text_items.items():
            port_x, port_y = port.pos().x(), port.pos().y()
            text_x, text_y = text.pos().x(), text.pos().y()
            port.setPos(port_x + x, port_y + y)
            text.setPos(text_x + x, text_y + y)
        for port, text in self._output_text_items.items():
            port_x, port_y = port.pos().x(), port.pos().y()
            text_x, text_y = text.pos().x(), text.pos().y()
            port.setPos(port_x + x, port_y + y)
            text.setPos(text_x + x, text_y + y)

    def init_node(self):
        """
        initialize the node layout and form.
        """
        # update the previous pos.
        self.prev_pos = self.pos
        # setup initial base size.
        self._set_base_size()
        # set text color when node is initialized.
        self._set_text_color(self.text_color)
        # set the tooltip
        self._tooltip_disable(self.disabled)

        # setup node layout
        # =================

        # arrange label text
        self.arrange_label()
        self.offset_label(0.0, 5.0)
        # arrange icon
        self.arrange_icon()
        self.offset_icon(5.0, 2.0)
        # arrange node widgets
        self.arrange_widgets()
        self.offset_widgets(0.0, 10.0)
        # arrange input and output ports.
        self.arrange_ports(padding_x=0.0, padding_y=35.0)
        self.offset_ports(0.0, 15.0)

    @property
    def id(self):
        return self._properties['id']

    @id.setter
    def id(self, unique_id=''):
        self._properties['id'] = unique_id

    @property
    def type(self):
        return self._properties['type']

    @type.setter
    def type(self, node_type='NODE'):
        self._properties['type'] = node_type

    @property
    def size(self):
        return self._width, self._height

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, width=0.0):
        w, h = self.calc_size()
        self._width = width if width > w else w

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, height):
        w, h = self.calc_size()
        h = 70 if h < 70 else h
        self._height = height if height > h else h

    @property
    def icon(self):
        return self._properties['icon']

    @icon.setter
    def icon(self, path=None):
        self._properties['icon'] = path
        path = path or ICON_NODE_BASE
        pixmap = QtGui.QPixmap(path)
        pixmap = pixmap.scaledToHeight(
            NODE_ICON_SIZE, QtCore.Qt.SmoothTransformation)
        self._icon_item.setPixmap(pixmap)
        if self.scene():
            self.init_node()

    @property
    def color(self):
        return self._properties['color']

    @color.setter
    def color(self, color=(0, 0, 0, 255)):
        self._properties['color'] = color

    @property
    def text_color(self):
        return self._properties['text_color']

    @text_color.setter
    def text_color(self, color=(100, 100, 100, 255)):
        self._properties['text_color'] = color

    @property
    def border_color(self):
        return self._properties['border_color']

    @border_color.setter
    def border_color(self, color=(0, 0, 0, 255)):
        self._properties['border_color'] = color

    @property
    def disabled(self):
        return self._properties['disabled']

    @disabled.setter
    def disabled(self, state=False):
        self._properties['disabled'] = state
        for n, w in self._widgets.items():
            w.widget.setDisabled(state)
        self._tooltip_disable(state)
        self._x_item.setVisible(state)

    @property
    def selected(self):
        return self.isSelected()

    @selected.setter
    def selected(self, selected=False):
        self.setSelected(selected)
        if selected:
            self._hightlight_pipes()

    @property
    def pos(self):
        return self.scenePos().x(), self.scenePos().y()

    @pos.setter
    def pos(self, pos=(0, 0)):
        self.prev_pos = self.scenePos().x(), self.scenePos().y()
        self.setPos(pos[0], pos[1])

    @property
    def name(self):
        return self._properties['name']

    @name.setter
    def name(self, name=''):
        if self.scene():
            viewer = self.scene().viewer()
            name = viewer.get_unique_node_name(name)
        self._properties['name'] = name
        self.setToolTip('node: {}'.format(name))
        self._text_item.setPlainText(name)
        if self.scene():
            self.init_node()

    @property
    def inputs(self):
        return self._input_items

    @property
    def outputs(self):
        return self._output_items

    def add_input(self, name='input', multi_port=False, display_name=True):
        """
        Args:
            name (str): name for the port.
            multi_port (bool): allow multiple connections.
            display_name (bool): display the port name. 

        Returns:
            PortItem: input item widget
        """
        port = PortItem(self)
        port.name = name
        port.port_type = IN_PORT
        port.multi_connection = multi_port
        port.display_name = display_name
        text = QtGui.QGraphicsTextItem(port.name, self)
        text.font().setPointSize(8)
        text.setFont(text.font())
        text.setVisible(display_name)
        self._input_text_items[port] = text
        self._input_items.append(port)
        if self.scene():
            self.init_node()
        return port

    def add_output(self, name='output', multi_port=False, display_name=True):
        """
        Args:
            name (str): name for the port.
            multi_port (bool): allow multiple connections.
            display_name (bool): display the port name. 

        Returns:
            PortItem: output item widget
        """
        port = PortItem(self)
        port.name = name
        port.port_type = OUT_PORT
        port.multi_connection = multi_port
        port.display_name = display_name
        text = QtGui.QGraphicsTextItem(port.name, self)
        text.font().setPointSize(8)
        text.setFont(text.font())
        text.setVisible(display_name)
        self._output_text_items[port] = text
        self._output_items.append(port)
        if self.scene():
            self.init_node()
        return port

    @property
    def widgets(self):
        return self._widgets

    def add_combo_menu(self, name='', label='', items=None, tooltip='test'):
        items = items or []
        label = name if not label else label
        widget = NodeComboBox(self, name, label, items)
        widget.setToolTip(tooltip)
        widget.value_changed.connect(self.set_property)
        self.add_widget(widget)

    def add_text_input(self, name='', label='', text='', tooltip='test'):
        label = name if not label else label
        widget = NodeLineEdit(self, name, label, text)
        widget.setToolTip(tooltip)
        widget.value_changed.connect(self.set_property)
        self.add_widget(widget)

    def add_widget(self, widget):
        if isinstance(widget, NodeBaseWidget):
            self._widgets[widget.name] = widget

    def get_widget(self, name):
        return self._widgets[name]

    @property
    def properties(self):
        return self._properties

    def add_property(self, name, value):
        if name in DEFAULT_PROPERTIES:
            return
        self._properties[name] = value

    def get_property(self, name):
        return self._properties.get(name)

    def set_property(self, name, value):
        if not self._properties.get(name):
            return
        if not isinstance(value, type(self._properties[name])):
            self._properties[name] = value

    def has_property(self, name):
        return name in self._properties.keys()

    def delete(self):
        for port in self._input_items:
            port.delete()
        for port in self._output_items:
            port.delete()
        if self.scene():
            self.scene().removeItem(self)

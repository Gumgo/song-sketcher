import drawing
import modal_dialog
import transform
import widget
import widget_manager
from units import *

class WidgetTests:
    def __init__(self, display_size):
        self._display_size = display_size

        root_h = widget.HStackedLayoutWidget()
        root_v = widget.VStackedLayoutWidget()
        scroll_area = widget.ScrollAreaWidget()
        scrollbar_h = widget.HScrollbarWidget()
        scrollbar_v_layout = widget.VStackedLayoutWidget()
        scrollbar_v = widget.VScrollbarWidget()
        scroll_area.horizontal_scrollbar = scrollbar_h
        scroll_area.vertical_scrollbar = scrollbar_v

        root_h.add_child(root_v, weight = 1.0)
        root_h.add_child(scrollbar_v_layout)
        scrollbar_v_layout.add_child(scrollbar_v, weight = 1.0)
        scrollbar_v_layout.add_padding(scrollbar_h.desired_height)
        root_v.add_child(scroll_area, weight = 1.0)
        root_v.add_child(scrollbar_h)

        root_inner_background = widget.BackgroundWidget()
        root_inner_background.color.value = (0.25, 0.25, 0.5, 1.0)
        scroll_area.set_child(root_inner_background)

        root = widget.HStackedLayoutWidget()
        root.desired_width = display_size[0] * 1.5
        root.desired_height = display_size[1] * 2.0
        root.margin = inches(0.25)
        root_inner_background.set_child(root)

        a = widget.RectangleWidget()
        a.color.value = (1.0, 0.0, 0.0, 1.0)
        a.border_thickness.value = points(4)
        a.border_color.value = (1,1,1,1)
        a.radius.value = inches(0.25)

        a.radius.transition().target(inches(1.25)).delay(2.0).duration(1.0).ease_in_ease_out()

        b = widget.VStackedLayoutWidget()

        c1 = widget.TextButtonWidget()
        c1.text = "Button"
        def show_dialog():
            layout = widget.HStackedLayoutWidget()
            btn = widget.IconButtonWidget()
            btn.icon_name = "metronome"
            layout.add_child(btn)
            btn.action_func = modal_dialog.show_modal_dialog(self._stack_widget, layout)
        c1.action_func = show_dialog

        c2 = widget.IconButtonWidget()
        c2.icon_name = "metronome"
        c2.action_func = lambda: print("Button!")

        c3 = widget.DropdownWidget()
        c3.set_options([(1, "Test option"), (2, "A very long option that's cut off"), (3, "Something else")])

        c4 = widget.SpinnerWidget()

        c5 = widget.InputWidget()

        d = widget.RectangleWidget()
        d.color.value = (0.0, 0.0, 1.0, 1.0)

        root.add_child(a, weight = 1.0)
        root.add_padding(inches(0.25))
        root.add_child(b, weight = 2.0)
        b.add_child(c1, weight = 0.0, horizontal_placement = widget.HorizontalPlacement.CENTER, vertical_placement = widget.VerticalPlacement.MIDDLE)
        b.add_child(c2, weight = 0.0, horizontal_placement = widget.HorizontalPlacement.CENTER, vertical_placement = widget.VerticalPlacement.MIDDLE)
        b.add_child(c3, weight = 0.0, horizontal_placement = widget.HorizontalPlacement.CENTER, vertical_placement = widget.VerticalPlacement.MIDDLE)
        b.add_padding(points(20.0))
        b.add_child(c4, weight = 0.0, horizontal_placement = widget.HorizontalPlacement.CENTER, vertical_placement = widget.VerticalPlacement.MIDDLE)
        b.add_padding(inches(0.25))
        b.add_child(c5, weight = 0.0, horizontal_placement = widget.HorizontalPlacement.CENTER, vertical_placement = widget.VerticalPlacement.MIDDLE)
        b.add_padding(inches(0.25))
        b.add_child(d, weight = 2.0)

        root_h.layout_widget((0.0, 0.0), display_size, widget.HorizontalPlacement.FILL, widget.VerticalPlacement.FILL)

        self._stack_widget = widget.StackWidget()
        self._stack_widget.push_child(root_h)
        widget_manager.get().set_root_widget(self._stack_widget)

    def shutdown(self):
        pass

    def update(self, dt):
        pass

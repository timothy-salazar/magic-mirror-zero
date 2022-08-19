""" The LinearColorTracker class uses the ColorComponent class to track red, 
green, and blue components moving with both horizontal and vertical gradients.
"""

class ColorComponent:
    """ This represents the magnitude of a color component (red, green, or
    blue), which is an integer somewhere between 0 and 255. This is used by the
    LinearColorTracker class to keep track of an RGB color which moves along
    some gradient.
    Calling __next__() will cause the magnitude of this component to increment
    by "inc".
    If 'bounce' is set to False, then when the magnitude of this component
    reaches its maximum, it will remain at its maximum value. The same is true
    should it reach its minimum value.
    If 'bounce' is set to True, when the magnitude of this component reaches
    its maximum or minimum value, it will "change directions" (if it was
    increasing by 10 each time __next__() was called, it will begin to decrease
    by 10 instead, and vice versus).
    The .change() method allows us to combine vertical and horizontal gradient
    components together within the LinearColorTracker class.
    """
    def __init__(
            self,
            value: int = 0,
            inc: float = 0,
            min_val: int = 0,
            max_val: int = 255,
            bounce: bool = False):
        """ Input:
                value: int - the initial value of the color component. Must be
                    an integer between min_val and max_val.
                inc: float - the amount by which the magnitude of the color
                    component should be incremented each time __next__() is
                    called. can be positive or negative.
                min_val: int - the minimum magnitude we want the color component
                    to take on.
                max_val: int - the maximum magnitude we want the color component
                    to take on.
                bounce: bool - when the magnitude of the color component reaches
                    min_val or max_val, if bounce is set to True, the component
                    will 'change directions' (if it was increasing by 10 each
                    time __next__() was called, it will begin to decrease by 10
                    instead, and vice versus).
        """
        if not (0 <= min_val <= 255):
            raise ValueError('''Invalid min_val passed to LinearColor class.
            RGB values must lie between 0 and 255''')
        if not (0 <= max_val <= 255):
            raise ValueError('''Invalid max_val passed to LinearColor class.
            RGB values must lie between 0 and 255''')
        if min_val >= max_val:
            raise ValueError(f'''Invalid min_val/max_val pair passed to
            LinearColor class. min_val must be less than max_val.
            min_val: {min_val} max_val: {max_val}''')
        self.max_val = max_val
        self.min_val = min_val
        if not self.in_range(value):
            raise ValueError(f'''Invalid value passed to LinearColor class.
            Attempted to initialize with value {value} and valid range of
            {min_val}-{max_val}.''')
        self.value = int(value)
        self.inc = inc
        self.step = 0
        # for bouncing
        self.bounce = bounce
        self.step_inc = 1

    def in_range(self, value: int):
        """ Returns True if value is within the range of allowed values
        """
        return (self.min_val <= value <= self.max_val)

    def val(self, step: int):
        """ Input:
                step: int - this value is increased each time .__next__() is
                    called, and it's reset whenever .change() is called.
                    Effectively, this represents either row number or column
                    number, depending on whether this ColorComponent instance
                    is being used to track a vertical or horizontal gradient.
            Output:
                val: int - the magnitude of the color component at the given
                    step.
        """
        # We're using round() here because I realized that there might
        # _conceivably_ be cases where a component might increase by an itty-
        # bitty amount, so I'm trying to make it alright for self.inc to be
        # a float.
        # We'll see - might revert later since the change in a component that
        # increases by less than 1 each step is probably unnoticeable.
        val = self.value + (step * self.inc)
        if val > self.max_val:
            val = self.max_val
            self.flip_step()
        if val < self.min_val:
            val = self.min_val
            self.flip_step()
        return int(round(val))

    def flip_step(self):
        """ This is used for the 'bounce' functionality. When it is called, it
        will reverse the sign of 'self.step_inc'. That means that, instead of
        'step' being increased by 1 each time .__next__() is called, it will
        decrease by 1 (or vice versus).
        """
        if self.bounce:
            if self.step_inc > 0:
                self.step_inc = -1
            else:
                self.step_inc = 1

    def change(self, val: int):
        """ Input:
                val: int - the new value for 'value'

        This overwrites the value of self.value with 'val' and resets self.step
        and self.step_inc to their initial values.
        In the context of the LinearColorTracker, this represents a newline.
        """
        self.step = 0
        self.value = val
        self.step_inc = 1

    def __next__(self):
        """ Returns the magnitude of the color component at the next timestep.
        """
        val = self.val(self.step)
        self.step += self.step_inc
        return val
        
class LinearColorTracker:
    """ This class uses the ColorComponent class to track red, green, and blue
    components moving with horizontal and vertical gradients specified by the
    horz_inc and vert_inc arguments.
    """
    def __init__(
            self,
            rgb: tuple = None,
            horz_inc: tuple = None,
            vert_inc: tuple = None,
            min_vals: tuple = None,
            max_vals: tuple = None,
            bounce: bool = False):
        """ Input:
                rgb: tuple of 3 ints - the initial values of the red, green, and
                    blue components of the color.
                horz_inc: tuple of 3 ints - the amount by which the red, green,
                    and blue components should be incremented for each column.
                vert_inc: tuple of 3 ints - the amount by which the red, green,
                    and blue components should be incremented for each row.
                min_vals: tuple of 3 ints - the smallest magnitudes that we want
                    the red, green, and blue components to reach
                max_vals: tuple of 3 ints - the largest magnitudes that we want
                    the red, green, and blue components to reach
                bounce: bool - if False, when the magnitude of a color component
                    reaches min_val or max_val, it will stay there. If True,
                    the color component will "bounce off the wall", and the
                    magnitude of the color component will begin to move in the
                    opposite direction
        """
        r, g, b = rgb if rgb else (0, 0, 0)
        # Did I remove the 'i' in 'horiz' here, resulting in a spelling
        # that doesn't show up anywhere else, just so these two lines would
        # line up neatly? Maybe...
        r_horz, g_horz, b_horz = horz_inc if horz_inc else (0, 0, 0)
        r_vert, g_vert, b_vert = vert_inc if vert_inc else (0, 0, 0)
        r_min, g_min, b_min = min_vals if min_vals else (0, 0, 0)
        r_max, g_max, b_max = max_vals if max_vals else (255, 255, 255)
        self.horiz = [
                        ColorComponent(r, r_horz, r_min, r_max, bounce),
                        ColorComponent(g, g_horz, g_min, g_max, bounce),
                        ColorComponent(b, b_horz, b_min, b_max, bounce)]

        self.vert = [
                        ColorComponent(r, r_vert, r_min, r_max, bounce),
                        ColorComponent(g, g_vert, g_min, g_max, bounce),
                        ColorComponent(b, b_vert, b_min, b_max, bounce)]

        # calling this here is a lazy way to fix some unwanted behavior.
        self.newline()

    def __next__(self):
        """ Returns a tuple of 3 ints, representing state of the color.
        """
        r, g, b = (color.__next__() for color in self.horiz)
        return r, g, b

    def newline(self):
        """ We're using this for text.
        If we have only horizontal gradients, it's expected that all the text
        in the first column should have the same color, and so on.
        If we have a vertical gradient, it's expected that the text in the first
        column should move along the gradient specified by vert_inc.
        This does that by resetting the horizontal color components to step 0,
        and replacing their 'value' attribute with the __next__() value returned
        by the corresponding vertical color component.
        """
        for vert_color, horiz_color in zip(self.vert, self.horiz):
            vert_inc = vert_color.__next__()
            horiz_color.change(vert_inc)

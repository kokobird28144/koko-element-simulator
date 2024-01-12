import wx


class NumberValidator(wx.Validator):
    def __init__(self):
        wx.Validator.__init__(self)
        self.valid_input = ['.', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        # self.string_length = 0
        self.Bind(wx.EVT_CHAR, self.on_char_changed)
        pass

    def on_char_changed(self, event):
        keycode = event.GetKeyCode()
        if keycode == 8 or (311 < keycode < 318):
            # self.string_length -= 1
            event.Skip()
            return

        input_char = chr(keycode)
        if input_char in self.valid_input:
            # if input_char == '.' and self.string_length == 0:
            #     return False
            # else:
            event.Skip()
            # self.string_length += 1
            return True
        return False

    def Clone(self):
        return NumberValidator()

    def Validate(self, parent):
        return True

    def TransferToWindow(self):
        return True

    def TransferFromWindow(self):
        return True
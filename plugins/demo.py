
import kaechatlib
from kaechatlib.ui.preferences import Page
from Tix import Label, BOTH

@kaechatlib.chat_command
def _demo(frame, cmd, args, args_eol):
    """/demo [RANDOM_ARGS...]

    Simple chat command demonstration.
    Echoes back the arguments to the current channel.
    """
    frame.echo("DEMO: args: %r, args_eol: %r" % (args, args_eol))
    frame.echo("See also: http://www.youtube.com/watch?v=dQw4w9WgXcQ")

class DemoPage(Page):

    # Identification string for the page. Must be unique with respect to other
    # pages. Please use only lowercase letters and underscores. Also, to reduce
    # the risk of conflict with other plugins, use a prefix based on the plugin
    # name.
    id = "demo_demo"

    # Text for the Tix.NoteBook tab label.
    label = "Demo"

    # Added as a Tix.Label at the top of the page.
    title = "This is how you add new pages to the Preferences window."

    def init_widgets(self):
        # This is called from the constructor to initialize subwidgets.
        # The default implementation does nothing.
        Label(self, text="""\
Never gonna give you up,
Never gonna let you down,
Never gonna run around and desert you,

Never gonna make you cry,
Never gonna say goodbye,
Never gonna tell a lie and hurt you.""").pack(fill=BOTH)

    def init_bindings(self):
        # This is called from the constructor to initialize event bindings.
        # The default implementation does nothing.
        # Please note: The oddity in separating widget initialization from
        # event bindings is a personal choice rather than something needed by
        # the implementation. It's perfectly feasible to initialize bindings in
        # `init_widgets' and leave this function out, or initialize everything
        # here and not implement `init_widgets'.
        pass

    def commit(self):
        # Called when either the "OK" or "Apply" buttons are clicked, and no
        # Page returns false from validate(). If you need to commit
        # configuration data, do it here.
        # The default implementation does nothing.
        pass

    def validate(self):
        # Called to perform self-validation when either the "OK" or "Apply"
        # buttons are clicked. Should return True if all is OK, or False if
        # something is wrong. If False is returned, commit() is not called,
        # and (in case this was invoked by pressing "OK") the window is not
        # closed.
        # The default implementation always returns True.
        return True

def on_prefswindow_create(window):
    # Called when a "Preferences" window is created. The `window' argument is
    # an instance of `kaechatlib.ui.preferences.PreferencesWindow'.
    window.add_page(DemoPage)

"""Icon names for button artwork.

Every picture in the UI is named here so the set stays consistent and a control
changes its artwork in one place. A value is the NAME OF AN ACTION rather than
a description of the picture ("switch", not "arrow"), because the caller is a
button that knows its own job; that is also what lets a picture be redrawn
without touching a line of calling code.

Each name resolves through `resource_paths.button_icon_path` to a file in the
generated icon directory. `generate_icons.py` derives every one of them from a
committed master, so the names here and the files there are two halves of one
contract, held by a structural test rather than by memory.

These were emoji once, written as escape sequences and sized by measuring the
font. Emoji theme themselves and need no packaging step, which is why they were
chosen; they were replaced because at a readable size their detail is coarse
and a set assembled from whatever the platform font happened to provide could
not be drawn in one visual language.

Author: Oliver Ernster
"""

# Device actions.
ICON_SWITCH = "switch"  # apply the selected profile to the devices
ICON_RESCAN = "rescan"  # look at the audio devices again
# The in-form combo refreshes do the same work as the rescan above, reloading
# the device list, so they deliberately wear the same picture. The name is kept
# separate because the buttons say different things about the same action.
ICON_REFRESH = ICON_RESCAN

# Profile actions.
ICON_NEW = "add-profile"
ICON_EDIT = "edit-profile"
# Both of these are composites: the prohibition bar over the icon of the thing
# being negated, so a delete reads as the stored profile struck through and a
# cancelled edit reads as the edit struck through.
ICON_DELETE = "delete-profile"
ICON_CANCEL = "cancel-edit"

# Editor actions.
ICON_SAVE = "save-profile"

# Window furniture.
ICON_QUICK_SWITCH = "quick-switch"
ICON_CONFIGURATION = "configuration"
ICON_HELP = "help-info"
ICON_DONATE = "donate"

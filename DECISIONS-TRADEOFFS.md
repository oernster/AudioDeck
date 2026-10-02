# Decisions and trade-offs

The deliberate choices Audio Deck rests on: what was chosen, what was given up
for it and why. Each entry is the decision as the product makes it today.
The detail behind each one, with the tests that hold it, lives in
[ARCHITECTURE.md](ARCHITECTURE.md) and [TESTING.md](TESTING.md);
[TECH_DEBT.md](TECH_DEBT.md) holds what only looks like debt and is left alone
on purpose.

## The product as a whole

### Local first, one person, one machine

Profiles are a JSON file in the platform's own per-user data folder. There is
no account, no cloud and no background service.

- **Rather than:** a server, an account or anything synchronised.
- **Gains:** nothing to sign in to; switching works with the network off; the
  profiles are one file that can be backed up by copying it.
- **Costs:** profiles belong to that machine and that user. Nothing follows
  them to another computer.

### It sets the system default; it does not route

A profile names one output device and one input device. Switching makes them
the operating system's defaults and stops there.

- **Rather than:** routing individual applications to different devices;
  mixing, effects or virtual cables.
- **Gains:** a small surface that works with every application that follows
  the system default.
- **Costs:** an application set to a specific device ignores the switch until
  it is set back to the default. Per-application routing needs another tool.

### One core, two front ends

The window and the command line are two clients of the same use cases. Each
has its own composition root; the switching logic exists once.

- **Rather than:** a command-line tool with its own switching code beside the
  window's.
- **Gains:** a Stream Deck button and the window switch a profile in exactly
  the same way.
- **Costs:** two composition roots to keep honest; a structural test names
  both so a third cannot appear unnoticed.

### Three platforms behind one set of seams

Windows, Linux and macOS each have their own audio backend behind the same
interfaces, chosen at start-up from the platform. The domain, the use cases,
the presenters and the command line are identical on all three.

- **Rather than:** Windows only.
- **Gains:** one product and one set of rules on every desktop.
- **Costs:** three backends to keep working, each tested over fakes at its
  seam rather than against real hardware.

## Privacy and the network

### One question asked of the network

The only call the application makes is to ask GitHub whether a newer release
exists. The request carries no identifier, not the application's version and
nothing about the profiles. It goes out with Python's default user agent,
which names the Python version and nothing more.

- **Rather than:** telemetry, usage figures or an account.
- **Gains:** nothing about the user or the profiles leaves the machine.
- **Costs:** no figures on which versions are in use or how the product is
  used.

### Only a published release can prompt

The check reads GitHub's latest-release address, which answers only with a
published release that is neither a draft nor a pre-release. A version that
cannot be read as numbers is never treated as newer.

- **Rather than:** listing every tag and filtering on the client.
- **Gains:** a tag pushed mid-development never prompts anybody; a malformed
  tag or a development build stays silent.
- **Costs:** nothing to fall back on if GitHub's own contract changed.

### Update checks: quiet unless there is news

A check runs a few seconds after launch and then once a day while the window
is open. An automatic check that fails or finds nothing says nothing. A
version the user skips never prompts again on its own; the check from the
Help menu reports every outcome and ignores the skip.

- **Rather than:** no check at all; one that reports every outcome; retries.
- **Gains:** updates are found without nagging; a skipped release stays
  reachable by asking.
- **Costs:** one unprompted request a day; an outage is invisible until the
  user asks.

### The update is fetched by the browser

Download hands the matching file's address to the default browser, falling
back to the release page. The application never downloads or installs an update
itself.

- **Rather than:** a self-updater.
- **Gains:** no code in the application that writes executables; the user
  sees exactly what is being fetched.
- **Costs:** installing the update is a step the user takes.

### Donations go through the browser

The donate button hands the payment page's address to the desktop and reports
it if the desktop declines to open a browser.

- **Rather than:** fetching the page itself.
- **Gains:** the one-call promise above is untouched by the button existing.
- **Costs:** Audio Deck never learns what happened next.

### Profiles are guarded; the skipped version is not

A profile that cannot be read or written raises an error the user sees. The
update check's one setting lives in a file of its own and is best effort: a
damaged file reads as nothing skipped and a failed write is swallowed.

- **Rather than:** one store with one set of failure rules.
- **Gains:** neither store's failure rules leak into the other; the user's
  own work is never lost quietly.
- **Costs:** a lost skip costs one extra prompt after the next release.

## Devices and switching

### A device that is off can still be chosen

Devices that are disconnected or disabled are listed with their state, so a
profile can be built round a Bluetooth headset that is switched off.

- **Rather than:** listing only the devices that are working now.
- **Gains:** profiles can be set up before the hardware is to hand.
- **Costs:** the lists are longer; an offline device has to be marked as such.

### A switch applies what it can

Each device in a profile is applied on its own. One that is missing, the
wrong direction or refuses to change is skipped and the user is told which
and why; the other is still applied.

- **Rather than:** failing the whole switch when one device is missing.
- **Gains:** a headset left off does not stop the speakers changing.
- **Costs:** a switch can half succeed, so the report has to say so plainly.

### A device is applied when it comes back

When a switch skips a device because it is unavailable, that device is
watched. The moment it reconnects the profile is applied again and the user
is told.

- **Rather than:** making the user switch again once the device is on.
- **Gains:** turning on a headset is enough.
- **Costs:** only the last profile switched to in the running window is
  watched; the wait is not remembered across a restart and the command line
  does not wait at all.

### A device is matched by identity and direction

A profile's device is looked up by its identifier and whether it is an output
or an input.

- **Rather than:** the identifier alone.
- **Gains:** a headset that appears as both an output and an input under one
  identifier (as it does on macOS) resolves to the right half.
- **Costs:** none recorded.

### On Windows, every role at once

A switch sets the chosen device as the default for all three Windows roles:
general, multimedia and communications.

- **Rather than:** the general default alone.
- **Gains:** call applications that follow the communications default move
  with everything else.
- **Costs:** a user who keeps a separate communications device cannot keep it
  through a switch.

### Events where the platform offers them, polling where it does not

Windows and Linux report device changes as they happen; macOS is polled every
few seconds. Every platform also rescans on a slower timer. A burst of changes
is folded into one rescan.

- **Rather than:** a CoreAudio listener on macOS, whose callback lifetime
  rules are a crash risk from Python; polling everywhere.
- **Gains:** prompt updates where the platform offers events; nothing that can
  dangle on macOS; a missed event is caught by the timer.
- **Costs:** on macOS the device list can be a few seconds stale.

### Device work never runs on the window's thread

Enumerating devices, switching and reading the current defaults run on a
background thread. The window only draws what comes back.

- **Rather than:** calling the audio system from the window directly, which
  freezes it during rescans and switches.
- **Gains:** the window stays responsive while devices come and go.
- **Costs:** status arrives a moment after it is asked for; the threading has
  to be owned and tested.

### Unprompted work fails quietly

Status reads, background rescans and the reconnect re-apply never raise a
dialog. Each broad handler states what it degrades to. A switch the user asked
for does report its failure.

- **Rather than:** surfacing every error the audio system raises.
- **Gains:** a device vanishing mid-scan, which is ordinary, never puts a
  dialog on screen out of nowhere.
- **Costs:** a persistent background fault shows only as stale status.

### Linux through command-line tools

The Linux backend drives the sound server through its own command-line tools:
PulseAudio's client tools first, PipeWire's own where those are absent or
refused.

- **Rather than:** a Python PulseAudio library.
- **Gains:** no extra Python dependency; JSON output keeps the parsing
  testable; both PulseAudio and PipeWire desktops work.
- **Costs:** a system running bare ALSA with neither sound server is not
  supported.

### The Flatpak asks the host to make the change

PipeWire refuses sandboxed clients permission to change the default device.
Inside the Flatpak the metadata write is therefore run in the host session,
which is why the Flatpak asks to talk to the Flatpak service.

- **Rather than:** a sandboxed build that can list devices but never switch
  them.
- **Gains:** switching works from the Flatpak.
- **Costs:** a broader sandbox permission than a device switcher would
  otherwise need.

### macOS through ctypes with every signature declared

CoreAudio is called through ctypes, with each C function's argument and return
types stated explicitly. Devices are identified by their UID.

- **Rather than:** pyobjc; ctypes' default marshalling, which is unreliable on
  Apple Silicon; the numeric device ID, which changes across reboots and
  unplugs.
- **Gains:** no heavyweight dependency for a handful of calls; profiles
  survive a reboot.
- **Costs:** the binding is Audio Deck's own to maintain.

## Profiles and the command line

### Profiles are named exactly

The command line finds a profile by its exact name, case included. Two
profiles may not share a name.

- **Rather than:** loose matching.
- **Gains:** a Stream Deck button names one profile and only one.
- **Costs:** a name typed with different capitals is not found; the error
  lists the names that exist.

### The exit code says whether anything changed

A switch from the command line exits successfully only when at least one
device was applied; skipped devices are listed on the error stream.

- **Rather than:** success whenever the profile was found.
- **Gains:** a script or macro can tell a switch that did nothing from one
  that worked.
- **Costs:** none recorded.

### The command line names the platform's own command

What the command line prints about running itself names the executable on
Windows, the bundle's executable on macOS and the Flatpak on Linux.

- **Rather than:** naming the Windows executable everywhere.
- **Gains:** the advice works on the machine it is printed on.
- **Costs:** none recorded.

### One window; the command line is never blocked

Only one window may run per user. On Windows a second launch brings the
existing window forward; on Linux and macOS it simply exits. The command line
is not guarded at all.

- **Rather than:** several windows; a guard over every launch.
- **Gains:** two windows never race over one profiles file; a Stream Deck
  button switches profiles while the window is open.
- **Costs:** on Linux and macOS a second launch appears to do nothing, because
  neither lets one program reliably raise another's window.

### The guard is one kernel operation and fails open

The guard is a named mutex on Windows and a locked file on Linux and macOS. If
the lock cannot be created at all, the application starts anyway.

- **Rather than:** a lock file checked by hand, which a crash can leave stale;
  refusing to start.
- **Gains:** a crash never leaves the application unable to launch.
- **Costs:** where the lock cannot be made, the single-window promise does not
  hold.

## The interface

### Every button is a picture

Every control in the window draws artwork generated from committed source
images. Delete and cancel share one prohibition bar laid over the picture of
what they negate. Each button names itself in a tooltip. The pictures share
one height and each button is as wide as its own artwork, so the row sits on
one baseline; the window is never narrower than the row it carries. Only the
generated set ships; the large source images stay in the repository.

- **Rather than:** emoji, which theme themselves and need no packaging step;
  pictures squared to one box, which makes the wide ones shorter than their
  neighbours.
- **Gains:** one visual language at a readable size, which emoji drawn from
  whatever font is present cannot give; small packages.
- **Costs:** the artwork has to be generated, staged by every build and
  checked; button widths vary along the row.

### Two view buttons over one stack

Quick Switch and Configuration are two buttons in the header over a stack of
pages; the button for the view already showing is disabled.

- **Rather than:** a tab strip.
- **Gains:** the header holds every control in one row of pictures; the
  keyboard model has no strip to walk.
- **Costs:** none recorded.

### Dark by default, drawn the same everywhere

The application sets its own style, palette and stylesheet on every platform:
dark unless the user picks light, with the choice remembered. Each theme carries
its own ring colours, since a green that reads on near-black is weak on white.

- **Rather than:** following the desktop's theme.
- **Gains:** the same look inside the Flatpak, where Qt has no desktop theme
  to follow, as anywhere else.
- **Costs:** the application does not follow the system's own light or dark
  setting.

### A switch shows what a press will do

The theme toggle shows the sun while the window is dark, because a press
brings the light. The setup program's toggle follows the same convention with
the same artwork.

- **Rather than:** showing the current state.
- **Gains:** one convention in both programs.
- **Costs:** learned once.

### Everything reachable from the keyboard

Tab and the arrow keys walk one explicit ring through every control, wrapping
at both ends. A list is one stop whose items are walked with Up and Down.
Picture buttons take focus from the keyboard only, never from a click. A ring
marks a control, never the pane, list or scroll area holding it; a list shows
where the user is through its current item.

- **Rather than:** mouse-first controls; Qt's default focus policy, under which
  a mouse click leaves a ring on whatever was clicked; rings that reach a
  container and outline it whenever the pointer rests there.
- **Gains:** the whole window works without a mouse; a ring always means the
  thing about to be acted on.
- **Costs:** every new control needs its place in the ring.

### Tooltips show while another program has focus

Every top-level window, dialogs included, is marked as it is shown so its
tooltips appear even when it is not the active window. This has been checked
on Windows.

- **Rather than:** Qt's default of tooltips over the active window only, with
  each window opting in.
- **Gains:** a picture button can be identified without first clicking the
  window.
- **Costs:** none recorded.

### The guide is a key to the real buttons

Help then Guide reads the user guide file into sections and draws each
button's own artwork beside its name, so every word of the file reaches the
page.

- **Rather than:** a plain rendering of the file; screenshots.
- **Gains:** the guide cannot drift from the buttons; the words have one home.
- **Costs:** the guide follows the file's structure rather than being freely
  laid out.

### Reading dialogs read themselves

The guide, the licences and About scroll gently on their own and stop the
moment the reader takes over, resuming in place afterwards.

- **Rather than:** static pages.
- **Gains:** long text can be read hands free.
- **Costs:** none recorded.

## Building and installing

### A build that cannot run is not shipped

PyInstaller writes an executable even when it could not find a module. Every
build script reads its warning file afterwards and fails if a module the
application cannot run without is listed.

- **Rather than:** trusting the packager's success.
- **Gains:** a broken package fails on the build machine rather than in a
  user's hands.
- **Costs:** the list of required modules must be kept up to date.

### Installed for one user, without administrator rights

On Windows the setup program installs into the user's own programs folder and
registers itself under the user's own part of the registry.

- **Rather than:** a machine-wide install.
- **Gains:** no administrator prompt.
- **Costs:** each account on a machine installs separately.

### A setup program of its own

Install, update, downgrade, repair and removal are one bespoke program. One
reading of the machine picks the route and the route decides the screen, its
heading, its options and its buttons. Work moves to a progress screen that
offers nothing; every path ends on a screen saying how it went. Repair
restores only the files that are missing or damaged, checked against what the
build recorded.

- **Rather than:** a generic installer; options greyed out in place while the
  work runs, where a disabled ticked box can read as unticked; a repair that
  rewrites every file.
- **Gains:** one identity throughout; a heading can never disagree with the
  route; a repair touches nothing that is already right.
- **Costs:** the setup program is Audio Deck's own to maintain.

### Offer to close a running copy first

Windows locks a running program's files, so the setup program checks first
and offers to close Audio Deck. It waits until the process has actually gone
rather than trusting the exit code of the request. The request names the
program alone and never asks to end its whole process tree.

- **Rather than:** failing at the first locked file with a path in the error;
  ending the process tree, which can count the setup program itself as a
  descendant and end it.
- **Gains:** an update over an open copy just works; declining changes
  nothing and says what to do.
- **Costs:** none recorded.

### Removing the application leaves the profiles

Uninstalling removes the program and its registration. The profiles folder is
left where it is; the screen says so.

- **Rather than:** removing the user's data with the program.
- **Gains:** reinstalling later picks up where the user left off.
- **Costs:** a user who wants everything gone deletes one folder by hand.

### The setup program wears its own stylesheet

The setup program uses the same artwork-derived palette as the application
but its own ring model: a green ring on hover or focus and a red one while
disabled.

- **Rather than:** layering the application's stylesheet over it.
- **Gains:** neither program's ring rules fight the other's.
- **Costs:** two stylesheets to keep in step.

### Each platform built by its own tools

Windows is built with PyInstaller into a single executable wrapped by the
setup program; macOS is a disk image that is signed, notarised and stapled;
Linux is a Flatpak built from wheels downloaded beforehand, so the sandboxed
build needs no network. The macOS build fails rather than produce an
unnotarised image unless that is asked for explicitly.

- **Rather than:** one cross-platform packager; an unsigned macOS build.
- **Gains:** each package is built by the tools that know its platform;
  Gatekeeper opens the macOS one without warnings.
- **Costs:** a machine of each kind to build on; an Apple developer account
  for the signing.

### Two licences plus a commercial one

The backend is GPL-3.0 and the PySide6 interface LGPL-3.0, matching Qt's own
licensing. A commercial licence for the author's own code is offered
separately.

- **Rather than:** one licence for everything.
- **Gains:** the interface can be reused under the lighter terms Qt itself
  carries.
- **Costs:** a licence map and two licence texts to keep straight; the
  application shows both under Help.

### The website's stylesheet is addressed by its content

Each local stylesheet and script link on the website carries a fingerprint of
the file it points at, so a changed file gets a new address.

- **Rather than:** relying on the browser cache expiring.
- **Gains:** a new page never arrives paired with the old stylesheet; an
  unchanged file keeps its address and its cache.
- **Costs:** the fingerprints must be refreshed after editing the site's
  styles.

## Engineering

### Layers held by tests

The code is split into domain, application, infrastructure and presentation,
each depending only inward. Platform code sits behind Protocols; only the two
composition roots name a concrete class; no module builds a service at import
time. Structural tests scan the imports to hold each rule.

- **Rather than:** convention alone.
- **Gains:** the rules about profiles and switching are tested with no audio
  hardware, disk or screen; a broken boundary fails the build.
- **Costs:** more modules and more explicit wiring.

### Presenters hold the logic; views are passive

The window follows model, view and presenter: views call presenters,
presenters call use cases and report back with Qt signals.

- **Rather than:** logic inside the widgets.
- **Gains:** behaviour is tested through presenters without driving the
  screen.
- **Costs:** view construction sits outside the coverage gate and is judged by
  running the application.

### Complete coverage of what can be measured

The suite fails below complete statement and branch coverage over the
package. A short list of paths is excluded, each with a written reason:
package markers, the composition root, view construction and the Windows
modules that would change the machine's real default devices if run.

- **Rather than:** a lower figure; tests that change the developer's audio
  while they run.
- **Gains:** a gap is a missing test or dead code, never noise.
- **Costs:** the excluded modules rely on their seams being faked faithfully.

### Tests with real parts

No mocking library is used. Doubles are hand written; Qt is never mocked and
runs offscreen; the JSON stores are tested against real files. Guards are
proved by planting a violation and watching them fail.

- **Rather than:** mocks and assumed guards.
- **Gains:** a passing test means the real thing works; a guard is known to
  bite.
- **Costs:** fakes are written and maintained by hand.

### Small modules

Every module in the package, the setup program and the tests sits under a
size cap; one that comes close is cut well below it rather than shaved by a
line. Delivery scripts are exempt, being linear recipes.

- **Rather than:** letting files grow until somebody notices.
- **Gains:** modules split at real seams; the cap is measured on every run
  rather than remembered.
- **Costs:** more, smaller files.

### One home for the version

The version lives in one file at the root of the repository. The application,
the package metadata and the build scripts read it; the documentation carries
none.

- **Rather than:** a version written wherever it is needed.
- **Gains:** a release changes one file and nothing drifts.
- **Costs:** the build scripts must read it rather than state it.

### Formatting and linting over the whole repository

Black and ruff are run without path arguments, so the build scripts and the
setup program are checked with the package; mypy checks the package with
untyped definitions disallowed. All three are run by hand rather than from
inside the test suite.

- **Rather than:** running them path-scoped, which leaves the build scripts
  and the setup program unchecked.
- **Gains:** the whole repository is held to the same standard.
- **Costs:** a step that relies on being remembered.

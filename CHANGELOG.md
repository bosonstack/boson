# Changelog

## [0.2.0]
- The objective of this release is to support mounting the Flint Metastore as a POSIX-like filesystem. Consequently, reducing the number of Docker volumes required by the Control Plane.
- The Experiment Tracker has been collapsed into the Experiment Server for simplicity and improved robustness around `inotify` events.
- The Experiment Server now stores metrics in the Flint Metastore via JuiceFS, which maintains a metadata database as a SQLite file inside the `storage_meta` mount.
- The Workspace now mounts the Flint Metastore to store workspace files such as notebooks. 
- Worker Containers also now mount the Flint Metastore, giving them visibility of workspace files. This enables notebooks to be executed within a notebook.

## [0.1.25]
- Redesigned networking to ensure control plane services communicate directly and not via `reverse-proxy`. This avoids circular service dependencies where `reverse-proxy` defines a route for `serviceX` and thus depends on `serviceX`, but `serviceX` depends on `serviceY` and tries to communicate with `serviceY` via `reverse-proxy` that is dependent on `serviceX`...

## [0.1.24]
- Added named volume for `workspace`.

## [0.1.23]
- First distributed release of FlintML. 

...

## [0.1.0]
- First build release of FlintML.

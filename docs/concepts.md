# Concepts

## Flint Control Plane

FlintML contains all the necessary components to enable end-to-end machine learning workloads. It accomplishes this by running several Docker Compose services, constituting the control plane. The control plane network is managed by an internal [nginx](https://github.com/nginx/nginx) container. The key services are:

- **Storage:** Powered by [Zenko CloudServer](https://github.com/scality/cloudserver), the Storage service comprises the *data layer* upon which the [Flint Catalog](#flint-catalog) is built. This data layer is referred to as the Flint Metastore. Data is stored per the `storage_data` and `storage_meta` Docker volumes.
- **Workspace:** The Workspace service serves the FlintML user interface (JupyterLab skin + custom extensions.) A custom [KernelProvisioner](https://jupyter-client.readthedocs.io/en/latest/provisioning.html) communicates with the Compute Manager service. Mounts the Flint Metastore using [s3fs](https://github.com/s3fs-fuse/s3fs-fuse) and uses this mount as the JupyterLab working directory.
- **Compute Manager:** The Compute Manager orchestrates and controls all [Worker Containers](#worker-containers) via a configurable *driver*. All requests to start and stop Worker Containers are handled by this service.
- **Experiment Server:** Integrated with [Aim](https://github.com/aimhubio/aim), the Experiment Server acts as the controller for all ML experiments and serves the Aim UI. Metrics live in the Flint Metastore as chunks using [JuiceFS](https://juicefs.com/en/). JuiceFS maintains its metadata with a SQLite database inside the `storage_meta` volume, coupling the lifetime of metrics metadata to the liftetime of metrics data.

## Flint Catalog

The Flint Catalog is a novel and simplified approach to a data catalog. It provides a logical repository that sits on top of the physical locations of files in the Flint Metastore. This enables key capabilities around governance, search, discovery, lineage and reusability. FlintML will continue to deploy new such capabilities throughout development. **The Flint Catalog does not govern workspace files or metrics.**

The Flint Catalog defines an Item as logically being a Table (i.e. Delta), or an Object (incl. Artifact sub-type.) All Items are unified within the catalog and considered first-class data-citizens. Rather than logically grouping Items by way of a hierarchical structure like `<catalog>.<schema>.<entity>` as used in the Unity Catalog, the Flint Catalog allows for full flexibility through the use of tags.

Items can be tagged with `<key>=<value>` pairs to denote groupings such as `env=dev`, `proj=user-segmentation`, `user=peter`, `from=ingress-postgres`. Rather than shoehorning Items into a folder-like structure, you can group them together in whatever way best suits your desired taxonomy.

Importantly, Items are identified by their URI; an Item's URI is a url encoding of `<item-name>?<tag-key>=<tag-value>&...`. For example, you might have `user-purchases?source=postgres&env=staging`. No two Items of the same type can have the same URI.

## Worker Containers

FlintML's Control Plane does not execute user code (i.e. development notebooks and workflows.) This work gets delegated to Worker Containers. A Worker Container is a Docker container installed with the `flintml/worker-base` image (directly or indirectly by a derivative image.) 

Each Worker Container runs a single Jupyter kernel that communicates with the Workspace, Storage and Experiment Server services. **Therefore, it is crucial that the host running Worker Containers has networking to the host of the Control Plane.** Each Worker Container also mounts Workspace files to its working directory. This enables you to, for example, execute notebooks within a notebook: `%run ./root-level-notebook.ipynb`.

Worker Containers are instantiated by the [Driver](#drivers) configured for use by the Compute Manager service.

### Custom Images

To customise the compute environment of a Worker Container, you will need to write a custom image that is derived from `flintml/worker-base`. For example, you may want to install custom Python dependencies, CUDA, TensorFlow wheels etc.

You must then point to this custom image in the [worker configuration](../README.md#worker-configuration) file specified by the `DRIVER_CONFIG` [environment variable](../README.md#driver_config). For example:

```yaml
driver:
  type: local
  image: my-custom-worker
```

See the Docker [docs](https://docs.docker.com/reference/cli/docker/image/push/) to learn about how to push a custom image to a Docker registry. Note that you can push it to your local registry for quick iteration and convenience.

### Drivers

Drivers are the brains that the Compute Manager use to manage Worker Containers. Currently, only the Local Driver is implemented - which uses the host's Docker deamon to spin up/down containers. Future drivers wil be added to support tools such as Libcloud (i.e. cloud VMs), Docker Swarm, Kubernetes, Slurm, ECS etc.

You may implement your own custom Driver by following the [LocalDriver](../src/compute-manager/src/driver/local.py) implementation. It subclasses `BaseDriver` - but we acknowledge that this superclass is basically a no-op at the moment and intend to improve the abstraction to make it easier to write custom drivers.

#### Local Driver

As stated, the Local Driver uses the Control Plane host's Docker deamon to manage containers. Hence, when using this driver, the Docker socket must be mounted to the Compute Manager by populating the `DOCKER_SOCKET` [environment variable](../README.md#docker_socket).

The driver does not manage memeory or CPU limits. Although, we are actively investigating how to make this driver more robust.
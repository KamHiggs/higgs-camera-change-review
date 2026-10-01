# Isolated installation and manual setup

This wheel is a plugin for a separately supplied **InvenTree 1.5.6 / API 530** host, with **Python 3.12**. It is not an InvenTree installer. No database, account, dependency environment, native library or browser binary is included.

The demonstration used a fresh virtual environment, 154 pre-existing pinned dependency wheels installed offline, read-only existing host source/native libraries, a copy of a prior synthetic database, and new empty assessment storage. It therefore demonstrates this recorded installation route, not unattended setup on an arbitrary machine. Only macOS arm64 / CPython 3.12.14 is evidenced here.

## Install the unchanged wheel

With the isolated host environment active, use its Python:

```sh
python -m pip install --no-deps --no-index /path/to/public-package/dist/higgs_inventree_camera_review-0.1.3+correction.1-py3-none-any.whl
```

The path is a placeholder for the extracted package. Wheel SHA-256: `a065bf22182f61f8263667290e6f49999c2ebb7effa32ab9ff1f9e31b3c6a66a`.

Use InvenTree's existing plugin activation and static collection procedure (`collectstatic` and `collectplugins` were recorded). Configure a separate writable `HIGGS_STATE_ROOT`, `HIGGS_DIAGNOSTIC_DIR`, and an identifying `HIGGS_INSTANCE_ID` for the host. `HIGGS_REQUIRED_ASSURANCE` defaults to `HIGGS-RECORDED-DECISION-0.1.3` and is operator-controlled. Use the bundled pinned dependency by default. Do not point the plugin at a different dependency archive.

Use the unchanged wheel for the demonstrated build. Source is supplied for inspection; rebuilding it is not the artifact tested here. Wheel/pyproject license metadata retains preparation-time wording; the owner's current MIT grant is in [LICENSE_STATUS.md](../LICENSE_STATUS.md).

## Prepare the synthetic inventory explicitly

The current Part is review context, not an engineering-modeled incumbent. Create a substitute Part with exactly one manufacturer-part binding: manufacturer `Teledyne FLIR`, MPN `BFS-U3-51S5M`. Attach the following exact parameter names and dimensionless values to that substitute Part:

| Parameter | Demonstration value |
|---|---|
| `HIGGS_CAMERA_ID` | `CAM-FLIR` |
| `HIGGS_ISP_ENABLED` | `false` initially; later `true` |
| `HIGGS_PIXEL_FORMAT` | `Mono8` |
| `HIGGS_TRANSPORT` | `USB3-Vision` |
| `HIGGS_EVIDENCE_ID` | `d23cd87f6d842ceb850eba865bf1b19ce120a5185ccb58634dbdc622e05f78ee` |

Parameter units must be empty. The panel's fast-line requirement is `45` fps; other requirements remain in the fixed synthetic model, including the slow line's 30 fps. The requirement is request-local: history restores the saved assumption; this is not a maintained project-requirements system. The original [mapper contract](contracts/MAPPER_CONTRACT.json) describes these unchanged bindings; its older verification metadata is historical, while [the assurance contract](contracts/ASSURANCE_CONTRACT.md) describes current verification.

## Walk through the existing panel

Open the current Part's **Higgs camera review** panel and select the substitute. Review at ISP `false`, export, change the declared ISP mode to `true`, reopen the prior assessment, then review and export again. The mode control changes a stored declaration only. View permission permits analysis and record creation; changing mode requires part-change permission. The demonstration used a superuser and did not establish least-privilege behavior.

Use a local isolated host and synthetic data. A public network service, production deployment and hardware operation are outside this release. The [offline export verification](OFFLINE_VERIFICATION.md) is the smaller, self-contained route available without host setup.

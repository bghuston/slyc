# slyc

Dependency-aware development slices and contract-based deployment planning for large monorepos.

> **Disclaimer: Proof of Concept — inspection only**
>
> **Do not run, install, build, deploy, or otherwise execute anything from this repository.** This includes the CLI, example applications, bootstrap scripts, container configurations, editor tasks and automation workflows. The repository is provided for reading and architectural discussion only.
>
> Much of this project was built with **AI-Assisted Development workflows** for demonstrating and testing logic. That describes its exploratory purpose; it does not establish that the code or its logic has been tested, independently reviewed, or verified. Treat all code, configuration, documentation and outputs as untrusted illustrative material. Do not rely on them for correctness, security, reliability or deployment decisions, even if a check reports success.
>
> This project has a shallow Git history because it is based on proprietary codebases that could not be cloned into this public repository. The GitHub version is provided for illustrative purposes only and does not include the original codebases or their development histories. Here, “shallow history” describes the limited public development record, not a Git shallow-clone configuration.
>
> This repository is an experimental proof of concept exploring dependency-aware development slices and contract-based deployment planning for large monorepos.
>
> It is not actively maintained and is not intended for production use. Features, configuration formats, APIs and command-line interfaces may change without notice. No guarantees are provided regarding stability, security, compatibility or ongoing support.

## Concept

Monorepos offer shared history and atomic cross-project changes, but large checkouts can burden editors, toolchains and coding-agent context. Independently deployed services also introduce compatibility questions that source dependencies alone cannot answer.

`slyc` explores two distinct graphs:

- **Development slices:** which project sources and shared libraries belong together in a reduced working tree.
- **Lean deployment graph:** which consumer/provider contracts describe relationships between service versions.

The files illustrate these ideas. Their presence is not evidence that the design or implementation works.

## Development slices

A development workflow usually concerns one project and a small set of shared libraries, even when they live in a massive monorepo. Development slices are intended to make the checkout and environment match that scope:

- **Smaller source checkouts.** The model uses Git sparse checkout to materialize the selected project's files and its transitive development dependencies, plus essential repository metadata. Unrelated applications and services stay outside the working tree, reducing the files that local IDEs and cloud coding agents need to index, search and consider. Sparse checkout controls file visibility; partial clone is a separate mechanism for reducing the initial transfer of file contents.
- **Only the required toolchains.** The model derives editor and development-container configuration from the selected workflow, rather than provisioning every language used anywhere in the repository. Avoiding unrelated toolchains and dependency setup is intended to shorten cloud-agent startup and local environment preparation, while keeping IDE tooling focused on the work at hand.

For example, a Payments slice conceptually includes `services/payments/` and `packages/money/`, alongside repository metadata. Its Python workflow does not need the Node or Rust toolchains used by other projects. It also does not require Checkout's implementation merely because Checkout calls Payments at runtime.

Slice definitions live in `.slices/`; reusable editor/container configuration fragments live in `.configs/`. The committed `.workspace-graph.json` is a hand-authored **slyc-format** example, not native mise output. These files illustrate the design, not a supported environment to activate.

## Lean deployment graph

A small service change should not automatically become a release of every service that calls it. The lean deployment graph is intended to distinguish changes that can deploy independently from those that require coordinated or staggered releases.

```text
checkout
  ├── orders
  │    └── inventory
  └── payments
```

Arrows represent consumer → provider relationships. The deployment question is whether a proposed service version satisfies the contracts required by its actual consumers, including consumers still using an older client specification.

- **Determine whether a change breaks existing consumers.** A new provider version need not force consumers onto the newest client specification. If verification establishes that it still satisfies their existing contracts, those consumers should not need code changes or redeployment just because the provider changed. Compatibility is assessed against the relevant contracts and versions, rather than inferred from a shared release number.
- **Identify when staggered deployments are necessary.** A breaking change may require a compatible consumer update before a provider removes an old field or behavior. The graph must account for each intermediate combination of versions, not just the desired final state. If there is no supported sequence, or evidence is missing, it must not declare the rollout safe.
- **Keep the deployment scope proportional to the change.** When a change is compatible and only one service's artifact changes, the intended outcome is to deploy that service alone. Unchanged consumers can keep running. Compared with a monolithic release that restarts the whole application, this can avoid unnecessary worker restarts and repeated startup processes in unaffected components, reducing disruption and the scope of a deployment failure.

For example, a Payments update that preserves Checkout's existing contract could leave Checkout unchanged, even if Checkout uses an older client specification. Removing a field required by that client introduces a different question: whether a consumer update can first work with the old provider and then with the new one. The example fixtures explore that distinction; they do not establish a safe rollout.

Contracts can remain available independently of service implementation source. A developer could therefore work in a small Payments slice while retaining the metadata needed to reason about Checkout compatibility, without checking out or redeploying Checkout merely to make a local Payments change.

The Pact-shaped fixtures are hand-authored and unverified. Environment snapshots and service versions are illustrative data, not records of real deployments. Missing verification evidence means **UNKNOWN**, never compatibility. No fixture, output or CI result in this repository should be used to authorize a deployment.

## Example structure

| Project | Language | Development dependency | Runtime dependency |
| --- | --- | --- | --- |
| Checkout | TypeScript | api-types | Orders, Payments |
| Orders | Python | money | Inventory |
| Payments | Python | money | None |
| Inventory | Rust | inventory-core | None |

```text
slyc/                  Illustrative CLI and subsystem source
apps/checkout/         Checkout client source
services/              Orders, Payments and Inventory source
packages/              Shared type and domain library source
.slices/  .configs/     Slice and environment configuration examples
contracts/             Unverified Pact-shaped fixtures and version bindings
deployments/           Static environment and compatibility scenarios
scripts/  .github/     Untrusted validation and automation examples
```

Bootstrap and automation files are retained as source artifacts for inspection, not as supported ways to use this repository. Workflow examples have `.disabled` suffixes so GitHub Actions does not execute them. There are no setup or installation instructions.

## Maintenance and license

This repository is not actively maintained. Issues, pull requests and support requests may receive no response. See [contribution notes](CONTRIBUTING.md).

Copyright (c) 2026. **All rights reserved.** This repository and its contents are copyrighted; no open-source license or permission to reuse the material is granted. See [LICENSE](LICENSE).

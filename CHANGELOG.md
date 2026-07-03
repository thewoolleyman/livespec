# Changelog

## [0.6.1](https://github.com/thewoolleyman/livespec/compare/v0.6.0...v0.6.1) (2026-07-03)


### Bug Fixes

* prune dead project plugin registry entries ([8f56eb8](https://github.com/thewoolleyman/livespec/commit/8f56eb813fb0479c6f7d675d9a558ce1c519dde0))

## [0.6.0](https://github.com/thewoolleyman/livespec/compare/v0.5.0...v0.6.0) (2026-07-03)


### Features

* add credential_wrapper config key (schema+dataclass+validator) ([97b3d00](https://github.com/thewoolleyman/livespec/commit/97b3d00538f8b8b720b7a9bbe19709db7c306e56))
* add github auth guard template test ([49ab40d](https://github.com/thewoolleyman/livespec/commit/49ab40dc4ae159dc79159f62ffd1c8f26ced750d))
* warn-vs-fail lever for credential_wrapper callability ([47f8977](https://github.com/thewoolleyman/livespec/commit/47f8977be8e9254cce7dcf5fd6b3edd6a0b55e3e))


### Bug Fixes

* add doctor static spec target coverage ([8486f95](https://github.com/thewoolleyman/livespec/commit/8486f955c07d0e280ef34ada77b4735068611f30))
* add fastjsonschema facade cache ([ee9f17f](https://github.com/thewoolleyman/livespec/commit/ee9f17f8dab7958667dea609a191feee036dbdbf))
* add typed structlog facade ([10e1a0d](https://github.com/thewoolleyman/livespec/commit/10e1a0d4487e6eec107605fc2e08df4444530209))
* anchor relative propose-change spec target ([30588b0](https://github.com/thewoolleyman/livespec/commit/30588b0d8d37ff7b76f6a99e4393420698bf47de))
* rename copier template path templates/impl-plugin -&gt; templates/orchestrator-plugin ([a304b09](https://github.com/thewoolleyman/livespec/commit/a304b096cffffdf8244b54750afde18f2b12f048))
* resolve stale worktree repo names ([61beec7](https://github.com/thewoolleyman/livespec/commit/61beec7c8df2bd8ffa40eb19685a58b1145f9883))

## [0.5.0](https://github.com/thewoolleyman/livespec/compare/v0.4.0...v0.5.0) (2026-06-29)


### Features

* **doctor:** agents-ai-reference-resolution static check — AGENTS.md .ai/ refs must resolve ([b288fdb](https://github.com/thewoolleyman/livespec/commit/b288fdbf164f26ddfb940101d3c5071b1004baf8))
* **governed-lifecycle:** core bootstrap delegates to local reconcile verb (livespec-zs22.8.2) ([147b0d7](https://github.com/thewoolleyman/livespec/commit/147b0d7ede695e9f56b44f0c5f1794f90ab2ac9e))
* **template:** propagate .ai/ agent-instruction scaffold into impl-plugin template ([9dad852](https://github.com/thewoolleyman/livespec/commit/9dad852d695e2e34ee81f9f2ab56b7a4d6f85587))


### Bug Fixes

* catch stale repo-qualified spec citations ([4e859ec](https://github.com/thewoolleyman/livespec/commit/4e859ec690b52ab260bec234e4ca8005169016ba))
* scan Rust source citations ([1584c14](https://github.com/thewoolleyman/livespec/commit/1584c14c6febae18af7526dac60cd2092086e6a3))
* tighten repo-qualified citation matching ([0638e2b](https://github.com/thewoolleyman/livespec/commit/0638e2b245a0d92952eb4c824e8eeaf38511c933))
* tolerate release-please version-anchor bumps in doctor out-of-band-edits ([75110d0](https://github.com/thewoolleyman/livespec/commit/75110d0fa9e38eae6af8f8418353bfe5a65f84ba))

## [0.4.0](https://github.com/thewoolleyman/livespec/compare/v0.3.0...v0.4.0) (2026-06-26)


### Features

* **dev-tooling:** add cli-explicit-project-root check (livespec-besm.2) ([d32ea6d](https://github.com/thewoolleyman/livespec/commit/d32ea6d733518dc52caa1ebc24b64b95caacf007))
* **dev-tooling:** add no-renderer-vendoring check (livespec-besm.1) ([046f00e](https://github.com/thewoolleyman/livespec/commit/046f00e195607324759c73b649ae77f58d7f6820))
* **dev-tooling:** smoke check parses the rendered justfile under `just` ([92c43e8](https://github.com/thewoolleyman/livespec/commit/92c43e8ae6821f466b20778edbb68e5d61510eb3))
* **doctor:** reference-discipline static checks (no-cross-spec-reference, no-spec-section-citation-in-code) ([e0a67ec](https://github.com/thewoolleyman/livespec/commit/e0a67ec99ccec9b685f609dc4a40f26ecf8d641a))
* **doctor:** version-contiguity check fails on a vNNN history gap ([29b6860](https://github.com/thewoolleyman/livespec/commit/29b6860359b02c33588cd5bb91666d0f304e48c8))
* **template:** server-side branch-protection tripwire for the worktree pack ([68e4a02](https://github.com/thewoolleyman/livespec/commit/68e4a027f35f9e52d48a86edf30d9d9e72ed306e))
* **template:** worktree-discipline pack phase 2/3 — ecosystem profiles + copier questions + adapters ([c2a50c8](https://github.com/thewoolleyman/livespec/commit/c2a50c8d7b054971afd97bb515113f1df679fc00))


### Bug Fixes

* **template:** make the bootstrap recipe a shebang recipe so the justfile parses ([2a13391](https://github.com/thewoolleyman/livespec/commit/2a133911e513f1380f2547584ddc1f0cb82b3bbc))

## [0.3.0](https://github.com/thewoolleyman/livespec/compare/v0.2.0...v0.3.0) (2026-06-25)


### Features

* collapse spec_files kind to markdown-only; remove diagram-rendering machinery ([1469f10](https://github.com/thewoolleyman/livespec/commit/1469f10bd0248e0cc4696694afdd175f0bc23484))

## [0.2.0](https://github.com/thewoolleyman/livespec/compare/v0.1.0...v0.2.0) (2026-06-24)


### Features

* add render_commands to livespec_config validation ([8387bc5](https://github.com/thewoolleyman/livespec/commit/8387bc554379f4313358041a4801595e31d8acc9))
* add v2 spec_files manifest to template_config validation ([9bd4fe3](https://github.com/thewoolleyman/livespec/commit/9bd4fe3efe22084f843d8dbb9d0c7d9116f629e2))
* **codex:** add adapter sync check ([791cd38](https://github.com/thewoolleyman/livespec/commit/791cd3818925193572394b592fb85e8fa3624db4))
* config-name the spec-side CLIs and orchestrator in .livespec.jsonc ([26d6a9c](https://github.com/thewoolleyman/livespec/commit/26d6a9c4b07488bbf8596ed1bc9f0e81515dc6eb))
* **deps:** consume livespec-dev-tooling@v0.1.0 via uv git source ([05c11b4](https://github.com/thewoolleyman/livespec/commit/05c11b4a569f95b03bf0adfe53c95524b9d5f3db))
* deterministic reap-stale-worktrees action for orchestrator worktree hygiene (li-wtreap WI-2) ([e65ba42](https://github.com/thewoolleyman/livespec/commit/e65ba42fb78c81790d0ca9a221a1f495a505e5ff))
* **dev-tooling:** behavior_scenario_link advisory clause-to-scenario check ([a5d2229](https://github.com/thewoolleyman/livespec/commit/a5d2229595e1bc1dde6925ae4781d353f0801017))
* **dev-tooling:** single-source spec-clause extractor + gap-id primitive ([b3ac52b](https://github.com/thewoolleyman/livespec/commit/b3ac52bef96b3eb2efe2e74cd5720c38cb41e996))
* **doctor:** add wiring-completeness-cross-repo invariant (li-dctxr) ([25529ca](https://github.com/thewoolleyman/livespec/commit/25529ca90cb8a2a6d43d0ca48ccf8391ac9889c1))
* **doctor:** fix wiring-completeness-cross-repo for CI + complete Phase 3a (li-unbarliv, epic li-unbare) ([815fdda](https://github.com/thewoolleyman/livespec/commit/815fddadd98424654a0c71b36dd77a196436a386))
* **doctor:** implement no-orphan-blocker + no-duplicate-gap-id ([#148](https://github.com/thewoolleyman/livespec/issues/148)) ([4a9db48](https://github.com/thewoolleyman/livespec/commit/4a9db48e8358acf595b9d7b1ed7858cc6963c356))
* **doctor:** implement no-stalled-epic cross-boundary invariant ([#147](https://github.com/thewoolleyman/livespec/issues/147)) ([f85d315](https://github.com/thewoolleyman/livespec/commit/f85d31549f15f1a839c336dd7dfbb69b546b1393))
* **doctor:** plugin-agnostic work-item provider seam for cross-boundary checks ([4be4780](https://github.com/thewoolleyman/livespec/commit/4be47806f62a1249a52950f451c7e82b50322921))
* **doctor:** two cleanup invariants — no-stale-merged-branch + no-stale-worktree (li-f5wmjr) ([#177](https://github.com/thewoolleyman/livespec/issues/177)) ([ce2d400](https://github.com/thewoolleyman/livespec/commit/ce2d400c50beaec4f596e32fe0178129a00049dc))
* implement the config-named-cli-callability doctor invariant ([9f46cc8](https://github.com/thewoolleyman/livespec/commit/9f46cc8f82f1dfa36167b60d06dfd5248baf4ef1))
* manifest-aware doctor — diagram drift check + template-files-present rewiring ([4942c9a](https://github.com/thewoolleyman/livespec/commit/4942c9aeb5d51aa6f211cad699c849ab1ca71108))
* read next.prune_history_threshold from .livespec.jsonc in the next CLI ([5cbb22a](https://github.com/thewoolleyman/livespec/commit/5cbb22ac8c1109fb37e2765ff10619deacc6bfda))
* realize next wrapper contract shape — candidates[] + pagination via --limit/--offset ([a194b9d](https://github.com/thewoolleyman/livespec/commit/a194b9de87b1bb8497c9f8bb19645099663c98df))
* register livespec-with-diagrams as a built-in template name ([9a947d3](https://github.com/thewoolleyman/livespec/commit/9a947d3b947db7c3b179ee20c5ac5878e3f66a6d))
* retire the six work-item cross-boundary doctor invariants ([c6861e0](https://github.com/thewoolleyman/livespec/commit/c6861e0e959cd9c620410223c85d951b0641db30))
* retire the stale-cleanup doctor checks per the v105 catalogue ([01e07e2](https://github.com/thewoolleyman/livespec/commit/01e07e2c4d84e31539c7d803d462e67b7b282b03))
* revise render-lifecycle integration for diagram_source writes ([3471423](https://github.com/thewoolleyman/livespec/commit/3471423c46a3e246b74d6b97eaf0c3485a212bd5))
* **schema:** add parent_proposed_change field to proposed-change front-matter (li-ymwpk2) ([64f4b93](https://github.com/thewoolleyman/livespec/commit/64f4b9391c4f224044f2ffb5f79189c5507cbb67))
* **spec:** land v070 — declare livespec-dev-tooling shared-code mechanism ([a19ca03](https://github.com/thewoolleyman/livespec/commit/a19ca0362f0f3a9bbc3c87116a8a894b9b665b9f))
* **spec:** land v072 — cross-repo dependency awareness (li-e7h6ki) ([4061d44](https://github.com/thewoolleyman/livespec/commit/4061d44dfff68921263d557a49ca4d50b00275cd))
* **spec:** propose declare-livespec-dev-tooling-shared-code-mechanism ([5258a86](https://github.com/thewoolleyman/livespec/commit/5258a86465fbc34f4d57aea5293ccf01575f96fa))
* **spec:** propose no-stalled-epic doctor invariant ([#143](https://github.com/thewoolleyman/livespec/issues/143)) ([bc098ef](https://github.com/thewoolleyman/livespec/commit/bc098eff8a6671eff22b8ca1575b62d934a0f79d))
* **spec:** revise → v069 — accept no-stalled-epic invariant ([#146](https://github.com/thewoolleyman/livespec/issues/146)) ([813d7a3](https://github.com/thewoolleyman/livespec/commit/813d7a3b85b674b4350e272257d054ac3e8fd47a))
* **spec:** v075 — factor detect-impl-gaps as thin-transport skill (li-qt7t5t) ([#184](https://github.com/thewoolleyman/livespec/issues/184)) ([20d859b](https://github.com/thewoolleyman/livespec/commit/20d859b017bc93d53d38628b86493c4a3d35deba))
* **template:** add Red test for canonical-slug-drift detection (li-jnjtpl) ([055294a](https://github.com/thewoolleyman/livespec/commit/055294a6566d28d2d96a0b48c4a41fac17bcd96e))
* **template:** wire impl-plugin template to consume livespec-dev-tooling ([c0a7393](https://github.com/thewoolleyman/livespec/commit/c0a7393ec85dfff2305151e1373ec71f911e8d66))


### Bug Fixes

* complete no_stale_worktree case (b) remote-gone detection (li-wtreap WI-1) ([6c6cf12](https://github.com/thewoolleyman/livespec/commit/6c6cf125ebe5e71cb6647aea9e22b74c1b17c449))
* degrade wiring-completeness-cross-repo to skipped when dev-tooling absent ([c4df6a0](https://github.com/thewoolleyman/livespec/commit/c4df6a0c2ed74962bda98278475a7adb7207eb50))
* **dev-tooling:** pin .copier-answers.yml in copier-template-smoke expected files ([ab10768](https://github.com/thewoolleyman/livespec/commit/ab1076858bbef664ca9df2646db8cc4fb5e1c46a))
* **doctor:** backfill revision lists only diverging files in Resulting Changes ([bbd08c6](https://github.com/thewoolleyman/livespec/commit/bbd08c6af336124349ae5ddf73946d1964bd23b8))
* **doctor:** detect host repo via slug-vs-basename match when manifest path mismatches (li-unbarliv) ([0389751](https://github.com/thewoolleyman/livespec/commit/03897511b4b87d8140f4218b7b2e47b7f890d9ab))
* **doctor:** narrow bcp14 static check to Shall only (li-mrtoei) ([0c90289](https://github.com/thewoolleyman/livespec/commit/0c90289994a500ac638d20941e5c27f39aaf8dd5))
* **doctor:** never auto-backfill above a freshly-cut working-tree revision ([af3ac7a](https://github.com/thewoolleyman/livespec/commit/af3ac7ab58de02e6c299fd2f0e47f79eccd1ab5e))
* **doctor:** pin copier-template-workflow-coverage corrective action to --vcs-ref=master ([f0498f6](https://github.com/thewoolleyman/livespec/commit/f0498f6220a84ce9ab9e181edc8b6a6a42fe3efb))
* **doctor:** scan past working-tree v-dirs for next OOB slot (mm-gzi7ej) ([d89e0da](https://github.com/thewoolleyman/livespec/commit/d89e0daff9b6a71e73ebc9c4e03d9b8575f34cd2))
* **doctor:** scope copier-template-workflow-coverage to copier consumers (li-k4gio6) ([bbc5dcb](https://github.com/thewoolleyman/livespec/commit/bbc5dcb18237699265440c5a61c0adea27d614a5))
* **doctor:** share template resolver across doctor + resolve_template ([8449825](https://github.com/thewoolleyman/livespec/commit/8449825d8fcc293e47c6775a59155769c2a11b02))
* **doctor:** surface missing proposed_changes/ as clean Finding (li-uh5ht2) ([952a601](https://github.com/thewoolleyman/livespec/commit/952a601ac6fa2b39c9c464b6fa4aec5c825eca8f))
* drop auto-update-branches.yml from REQUIRED_WORKFLOW_FILES ([9df946a](https://github.com/thewoolleyman/livespec/commit/9df946a47acd0f61251619a321fa24b7ef9acf90))
* force GET on the wiring-completeness GitHub justfile fallback ([6d37dca](https://github.com/thewoolleyman/livespec/commit/6d37dcaafd9d404d0948dcfe00f4a9edd91019fc))
* **lint:** drop unused noqa on is_host_repo env discard (li-unbarliv) ([8025609](https://github.com/thewoolleyman/livespec/commit/80256093ba449c22c4a16c75e33df91c66f5748b))
* make wrapper help exit successfully ([8d2bfef](https://github.com/thewoolleyman/livespec/commit/8d2bfefe3321276901c7c2da83efb0918eb52634))
* point copier-template-coverage doctor narration at NFR after family-infra relocation ([1832eb9](https://github.com/thewoolleyman/livespec/commit/1832eb90fb781955cf25565ba9fe0a825f8b9709))
* project canonical-slug set into committed copier-template data (livespec-2jsj) ([9dd8b1f](https://github.com/thewoolleyman/livespec/commit/9dd8b1f55c1041f31be1e9f9ce761c9b3a2bc9b0))
* reaper skips never-pushed in-progress worktrees (remote-absent != merged) ([69eac2a](https://github.com/thewoolleyman/livespec/commit/69eac2af1527f09cc387a221e414ab19cc58438b))
* recognize any per-project env wrapper in beads-access guard ([1cfbd24](https://github.com/thewoolleyman/livespec/commit/1cfbd24963a72b1ae4025a06cccd693ea7f68b00))
* **revise:** emit diagnostic before silent non-zero exit (li-revslnt) ([01834d1](https://github.com/thewoolleyman/livespec/commit/01834d1c718df1f7a68092c0d36b34b79817db81))
* **seed:** preserve pre-existing .livespec.jsonc verbatim (li-2qjqen) ([#227](https://github.com/thewoolleyman/livespec/issues/227)) ([9329b4f](https://github.com/thewoolleyman/livespec/commit/9329b4f01cc63479c404ad42f8e996afd62bc0b4))
* wrapper unsets git-injected GIT_DIR before lefthook to stop core.bare flip ([3be0f3b](https://github.com/thewoolleyman/livespec/commit/3be0f3ba54c02c8192e1826fba5e487c3ad499fa))


### Refactoring

* **checks:** drop .claude/skills/loop/SKILL.md from copier_template_smoke expected files ([931db1b](https://github.com/thewoolleyman/livespec/commit/931db1b8cfdc737bc4eabbb2764fdf61ce818434))
* **comments:** clean historical refs in livespec/ + dev-tooling/checks/ sources (li-nhz Step 2) ([#221](https://github.com/thewoolleyman/livespec/issues/221)) ([16b6470](https://github.com/thewoolleyman/livespec/commit/16b6470bb8fb2b3536e7363cc24587850bfb6cea))
* **comments:** clean historical refs in tests/{prompts,bin,dev-tooling} (li-nhz Step 2) ([#215](https://github.com/thewoolleyman/livespec/issues/215)) ([bab8ede](https://github.com/thewoolleyman/livespec/commit/bab8edefaaef396a86a7beaa6dfde3c1221d72dd))
* **comments:** clean historical refs in tests/livespec/{io,validate} (li-nhz Step 2) ([#216](https://github.com/thewoolleyman/livespec/issues/216)) ([04eec4b](https://github.com/thewoolleyman/livespec/commit/04eec4b32937a47d9e0ece49155d373f4884e5ce))
* **comments:** clean historical refs in tests/livespec/commands/ (li-nhz Step 2) ([#218](https://github.com/thewoolleyman/livespec/issues/218)) ([5c9c894](https://github.com/thewoolleyman/livespec/commit/5c9c894fed413c2c94c12fc42221d151705a8573))
* **comments:** clean historical refs in tests/livespec/doctor/ (li-nhz Step 2) ([#219](https://github.com/thewoolleyman/livespec/issues/219)) ([50308fa](https://github.com/thewoolleyman/livespec/commit/50308fa2babcacd0a30fc4139972cefe139218b9))
* **comments:** clean justfile + lefthook + release-tag historical refs (li-nhz Step 2) ([#214](https://github.com/thewoolleyman/livespec/issues/214)) ([e5f1375](https://github.com/thewoolleyman/livespec/commit/e5f13754b658e433b78c2be9347dbe2dd113962d))
* **doctor:** add depends_on-ref-wellformedness invariant (li-f2fbkl) ([e5a90f4](https://github.com/thewoolleyman/livespec/commit/e5a90f4aa996fe26d943f56d7de2ec0d2d280fe5))
* **doctor:** extend no-stalled-epic for non-local + typed-dict deps (li-f2fbkl) ([7790c03](https://github.com/thewoolleyman/livespec/commit/7790c03fbb933c1b13a019bbf8ad636863bb5fe7))
* **doctor:** NewType wraps for CheckId + SpecRoot in 14 static-check sites (li-xxjopf Step 3c) ([#196](https://github.com/thewoolleyman/livespec/issues/196)) ([dcb95b3](https://github.com/thewoolleyman/livespec/commit/dcb95b3e91a421f3a538df7e4f40d796f93b659a))
* **doctor:** rename no-orphan-blocker → no-orphan-dependency + add cross_repo parse shim (li-f2fbkl) ([dc7d5a2](https://github.com/thewoolleyman/livespec/commit/dc7d5a2b0c7191b0c74b643c6e039f03a6bd0834))
* **doctor:** wire 6 cross-boundary checks through the work-item provider seam ([27bfbf9](https://github.com/thewoolleyman/livespec/commit/27bfbf9789454aff9e59a0298130e07981fbf98e))
* **doctor:** wire resolve_ref into no-orphan-dependency (li-f2fbkl) ([8a83c7d](https://github.com/thewoolleyman/livespec/commit/8a83c7d9fe73c719caff80b184af1fd8596dabc9))
* **just:** rejoin check-types to the just check aggregate (li-xxjopf Step 4) ([#212](https://github.com/thewoolleyman/livespec/issues/212)) ([5305f62](https://github.com/thewoolleyman/livespec/commit/5305f6214711a18318df65b70599915f6f1407ab))
* **pyright:** drive the 3 step-3f stale-residual errors to zero (li-xxjopf Step 3f) ([#211](https://github.com/thewoolleyman/livespec/issues/211)) ([bffbc9d](https://github.com/thewoolleyman/livespec/commit/bffbc9d94c3fd61030cc51fb46a850e8238330fb))
* **pyright:** HKT erosion pragma for 14 remaining doctor/static modules (li-xxjopf Step 3e) ([#206](https://github.com/thewoolleyman/livespec/issues/206)) ([f0c5528](https://github.com/thewoolleyman/livespec/commit/f0c552805d009b7fd3080239d5c9ae9d70fa6e35))
* **pyright:** HKT erosion pragma for 7 commands/ helper modules (li-xxjopf Step 3e) ([09c874a](https://github.com/thewoolleyman/livespec/commit/09c874adac36c8ed7c0b2b9586fdd17f611d2ff6))
* **pyright:** HKT erosion pragma for commands/critique.py (li-xxjopf Step 3e) ([#202](https://github.com/thewoolleyman/livespec/issues/202)) ([8b09eae](https://github.com/thewoolleyman/livespec/commit/8b09eae31b2a046825d4f35fad6e7b50665b5d77))
* **pyright:** HKT erosion pragma for commands/next.py (li-xxjopf Step 3e) ([#198](https://github.com/thewoolleyman/livespec/issues/198)) ([839f837](https://github.com/thewoolleyman/livespec/commit/839f8372e1201955d6bdb4b6cb3ae7f64d3bca31))
* **pyright:** HKT erosion pragma for commands/propose_change.py (li-xxjopf Step 3e) ([#200](https://github.com/thewoolleyman/livespec/issues/200)) ([e675c43](https://github.com/thewoolleyman/livespec/commit/e675c43bb00717b8f8aef574a7847d5a3784a3f1))
* **pyright:** HKT erosion pragma for commands/prune_history.py (li-xxjopf Step 3e) ([#203](https://github.com/thewoolleyman/livespec/issues/203)) ([05000b8](https://github.com/thewoolleyman/livespec/commit/05000b856e913ffe7e1825ea5fba5cc3c43ac433))
* **pyright:** HKT erosion pragma for commands/resolve_template.py (li-xxjopf Step 3e) ([#204](https://github.com/thewoolleyman/livespec/issues/204)) ([aef04dc](https://github.com/thewoolleyman/livespec/commit/aef04dc0645b0b325891c646e922e426601cea62))
* **pyright:** HKT erosion pragma for commands/revise.py (li-xxjopf Step 3e) ([#201](https://github.com/thewoolleyman/livespec/issues/201)) ([31cf525](https://github.com/thewoolleyman/livespec/commit/31cf52512b5a71ce31a65fbba24bc6245306c90b))
* **pyright:** HKT erosion pragma for commands/seed.py (li-xxjopf Step 3e) ([#199](https://github.com/thewoolleyman/livespec/issues/199)) ([de92a61](https://github.com/thewoolleyman/livespec/commit/de92a61135fb1c7fbd7a0d542b0e66fd9e2ef330))
* **pyright:** HKT erosion pragma for doctor/run_static.py (li-xxjopf Step 3e) ([#208](https://github.com/thewoolleyman/livespec/issues/208)) ([af62767](https://github.com/thewoolleyman/livespec/commit/af627670c5db5ef1dd16835d6f07771cfc22718f))
* **pyright:** HKT erosion pragma for io/ layer (li-xxjopf Step 3e) ([#209](https://github.com/thewoolleyman/livespec/issues/209)) ([2b0b333](https://github.com/thewoolleyman/livespec/commit/2b0b33375729139d0cac9a6bcdf69f115ba17795))
* **pyright:** HKT erosion pragma for parse/front_matter.py (li-xxjopf Step 3e) ([#210](https://github.com/thewoolleyman/livespec/issues/210)) ([cf55d6b](https://github.com/thewoolleyman/livespec/commit/cf55d6b0afe1d59bd213f494cfbe9641d7cb157b))
* **pyright:** low-volume residual fixes (li-xxjopf Step 3d) ([#197](https://github.com/thewoolleyman/livespec/issues/197)) ([1ffb2fb](https://github.com/thewoolleyman/livespec/commit/1ffb2fb02b44741b432b259a854827870da01155))

## Changelog

All notable changes to the livespec plugin are recorded here.
This file is auto-maintained by release-please (see
`.github/workflows/release-please.yml` and
`SPECIFICATION/contracts.md` §"Plugin versioning"); do not edit it
by hand.

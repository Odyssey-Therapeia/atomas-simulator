# Contributing

## Welcome

Thanks for your interest in improving Nucleo.

We welcome:

- Bug reports
- Test coverage improvements
- Documentation improvements
- Feature proposals

For non-trivial changes, please open an issue first so we can align on scope
and direction before implementation. Small fixes and focused improvements can
be submitted directly as pull requests.

## Local Setup

Use Pixi to install dependencies and run the project locally:

```bash
pixi install
pixi run test
pixi run run
pixi run format
```

## Code Style

- Format Mojo code with `mojo format`
- Prefer `fn` over `def`
- Use descriptive variable names
- Add docstrings to public functions

## Pull Request Process

Before opening a pull request:

- Describe what changed and why
- Link the related issue when applicable
- Make sure the relevant tests pass
- Confirm that all submitted code and assets are original work

## What We're Looking For Right Now

We are especially interested in:

- Bug reports for edge cases in chain reaction logic
- Test coverage improvements
- Documentation improvements
- Reinforcement learning environment wrapper contributions

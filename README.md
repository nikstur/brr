# brr

Make your Nix builds go brr.

brr is a tool to evaluate and build a lot of derivations as fast a possible.

## Why brr?

Evaluating and building large sets of derivations with `nix-build` is quite
slow because it doesn't parallelize evaluation and doesn't parallelize
building. This makes maintaining parts of Nixpkgs that need a lot of testing
(e.g. systemd) annoying and slows down our ability to keep packages up to date.

brr aims to solve this problem by reliably and quickly building large attrsets
of derivations. Most importantly it focuses on quickly building NixOS tests.

Naturally, brr is thus focused on traditional non-flakes Nix usage. You point
it at an attrset and it goes brr.

brr aims to be hackable (it's a single python script) so that you can easily
extend it for your (weird and unusual) use cases without having to convince
anyone.

Of course if you think others have the same use case please do report back to
me!

## Usage

To build all tests of the systemd package:

```console
brr -A systemd.tests
```

You can point this to any attrset. Because brr relies on `nix-eval-jobs`, it will
forcibly walk the attrset and build all derivations it finds.

By default, this will not allow you to monitor progress directly (i.e. logs are
not directly printed to stdout). Only when a job is done, its logs are printed.

You can control the number of concurrent builds with `--jobs`.

### Monitor Build Progress with Tmux

You can monitor progress for your builds via tmux. First, you need to spawn a
separate tmux window. Open a new terminal window and start tmux.

```console
$ tmux
```

Back in your original window:

```console
$ brr -A systemd.tests --tmux
```

### Build on a Remote Builder

```console
$ brr -A systemd.tests --store ssh-ng://my-builder
```

Note that this will not copy back any results.

### Toposort Derivations

If you build a very large set of derivations it can be beneficial to toposort
them after evaluation but before actually building them.

```console
$ brr -A systemd.tests --toposort
```

## Technical Detail

brr leverages `nix-eval-jobs` to parallelize evaluation and `ninja` to
parallelize building and displaying progress.

This basic idea isn't from me. All credit is due to
[@pennae](https://git.lix.systems/pennae) for coming up with the idea and most
of the code.

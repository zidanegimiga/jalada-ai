# 0024. Web app layout

Status: Accepted
Date: 2026-11-17

## Context
The web app grew a flat `components/ui/` folder, a `lib/` folder that held everything from the API client to class name helpers, and features whose `components/` folders mixed components, hooks and test data. Each page wrapped itself in the app shell, so the header and bottom bar were rebuilt on every page change, which rules out a shell that stays in place and animates between pages.

## Options considered
1. **Keep the flat layout.** Nothing moves, but a new screen has no obvious home for its pieces.
2. **Shared, features and route groups, one folder per component.** The same split the API uses: shared building blocks, features that own their data and components, and routes that only compose.
3. **Group by file type (all hooks together, all components together).** Easy to find a kind of file, hard to see or remove a feature.

## Decision
Option 2.

```
apps/web/
  src/
    app/
      (app)/        signed-in pages; layout.tsx renders the shell once
        _components/  pieces only these routes use (AppShell, AppNav)
      (auth)/       sign-in and sign-up
      _components/  pieces only the root layout uses (Splash)
    features/<feature>/
      api/          calls the browser makes to /v1, one <feature>.api.ts
      server/       reads on the server, through shared/api/server-api.ts
      hooks/        state and effects shared by the feature's components
      components/<Name>/<Name>.tsx and index.ts
      types.ts, search.ts and other plain helpers at the feature root
    shared/
      components/<Name>/  building blocks with no feature knowledge
      api/          API client, generated types (api-types.ts) and schema helpers
      format/ styles/ config/ monitoring/
  tests/
    component/ unit/ support/
```

Rules:
- Routes compose features and shared pieces; they hold no logic of their own.
- A feature imports `shared/` and its own files. It may use another feature's types and server reads, never its components' internals.
- Shared code never imports a feature.
- Components are imported through their folder's `index.ts`.
- Styling stays Tailwind with the tokens in `globals.css` (decision 0008).

## Consequences
- A feature can be found, reviewed and removed as one folder, like an API module.
- The shell stays mounted between pages, which allows a sticky header, a floating bottom bar and page transitions.
- Moving a file means updating its imports; the type check finds any that are missed.

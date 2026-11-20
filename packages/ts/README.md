# linked-codebook (TypeScript)

Read, write and check codebooks of tables whose variables are linked to concepts.

```bash
npm install linked-codebook
```

The package has no dependencies and needs Node 22.18 or later, or a browser. It installs the command `linked-codebook`.
A [Python package](https://pypi.org/project/linked-codebook/) gives the same output.

```ts
import { build, fromRedcap, validate } from 'linked-codebook';

const profile = fromRedcap(text); // a REDCap data dictionary
const document = build(profile); // DSV JSON-LD
console.log(validate(document)); // []
```

Documentation: <https://bennokr.github.io/linked-codebook/docs/>. Source: <https://github.com/bennokr/linked-codebook>.

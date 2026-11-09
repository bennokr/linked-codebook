import constants from './generated/constants.json' with { type: 'json' };

export const {
  commands,
  enums,
  frictionless,
  inference,
  jsonld,
  redcap,
  condition,
  readstat,
  schema,
  sssom,
  table,
  vocabulary,
} = constants;

/** Templates of the IRIs that are written, by node kind. */
export const iris: Record<string, string> = jsonld.iris;

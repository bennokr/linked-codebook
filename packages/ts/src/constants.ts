import constants from './generated/constants.json' with { type: 'json' };

export const { commands, enums, inference, jsonld, schema, sssom, vocabulary } = constants;

/** Templates of the IRIs that are written, by node kind. */
export const iris: Record<string, string> = jsonld.iris;

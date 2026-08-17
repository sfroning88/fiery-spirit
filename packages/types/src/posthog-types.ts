export const POSTHOG_EVENTS = {
  cookie_banner_dismissed: "cookie_banner_dismissed",
  privacy_policy_opened: "privacy_policy_opened",
  privacy_policy_closed: "privacy_policy_closed",
  property_snapshot_created: "property_snapshot_created",
  shuffle_training_groups: "shuffle_training_groups",
  model_training_started: "model_training_started",
  model_prediction_requested: "model_prediction_requested",
  prediction_feedback_given: "prediction_feedback_given",
} as const;

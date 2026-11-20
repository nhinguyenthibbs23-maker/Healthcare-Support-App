# AI Use Appendix — GlucoGuide

## 1. AI tools used

The group used ChatGPT (OpenAI) as an AI-assisted development and writing tool during the development of GlucoGuide. The model/version shown for the current interaction was GPT-6. The group should check its chat history and add any other AI systems or model versions used by other members. The documented assistance took place during the project work, including 16–17 November 2026; group members should add any earlier or later dates from their own use.

## 2. How AI assistance was used

AI assistance was used for the following activities:

- **Python and model-development support:** Helped review the supplied project code and model-training workflow, explain the Scikit-learn pipeline and model metadata, and identify inconsistencies between code, saved metadata, and project documentation.

- **Course model comparison, thresholds, and PCA:** Helped add and run a reproducible hyperparameter search covering the classification algorithms from the course, add per-model cost-selected thresholds and an instructor-facing adjustable threshold explorer, compare validation precision and recall, and create a PCA component comparison table. The group reviewed this workflow as part of the final rebuild; the final selection, validation threshold, and held-out test metrics are summarized in the README and `DECISION_LOG.md`. The four group members should verify and own this disclosure before submission.

- **Streamlit application support:** Helped discuss the questionnaire flow and the use of `st.form` and `st.form_submit_button`, and draft an example form structure for collecting the five model inputs before submitting an assessment. Also provided guidance on organizing Streamlit pages, navigation, reusable components, and application structure.

- **UI/UX design and visual mockups:** Assisted in developing the visual direction for GlucoGuide, including its premium healthcare design style, colour palette, typography, sidebar navigation, cards, buttons, and page layouts. Generated visual design concepts and mockups for the Home, Risk Assessment, Results, Understanding Results, Health Tips, and About Model pages. Also suggested ways to maintain a consistent design system across the application.

- **User experience and interface planning:** Helped plan the user journey, questionnaire steps, information hierarchy, dashboard layout, and presentation of diabetes risk predictions. Provided recommendations for making the application more intuitive, accessible, visually consistent, and suitable for non-technical users.

- **Model documentation:** Helped review and draft explanations of the model, selected features, threshold, cost assumptions, evaluation metrics, Shapley-based explanations, intended use, and limitations for the README, decision log, and model card. Also suggested the structure and content of the About Model page to communicate the model's methodology, performance, explainability, and limitations.

- **Project quality review:** Reviewed the supplied project archive and highlighted items for the group to verify, including dependency completeness, form implementation, BMI handling, repository cleanup, and end-to-end application testing.

- **Writing and presentation support:** Helped improve the wording and structure of project documentation and explain technical concepts in Vietnamese so that group members could understand and discuss the implementation.

AI-generated suggestions, visual mockups, and drafts were treated as assistance, not as authoritative evidence or automatically validated implementation. The group remains responsible for deciding which suggestions to adopt and for checking all code, data, results, visual content, and statements before submission.
## 3. Verification and limitations

The supplied model metadata reports programmatically calculated evaluation metrics for the saved model. These values should be checked against the final saved model artifacts and regenerated if the group retrains the model. A code review or explanation provided by AI does not establish that the application has been fully tested.

Before submission, the group should:

- Review the complete source code and be able to explain the main implementation and modeling decisions.
- Run the tests and manually verify the complete Streamlit user journey in the final environment.
- Check dataset variable definitions and encodings against the original dataset and CDC documentation.
- Confirm that the final README, decision log, model card, application, and repository describe the same model, threshold, intended use, and limitations.
- Verify all reported metrics against the final model artifacts.
- Record any additional AI tools, model versions, dates, prompts, and uses that are not covered in this appendix.

GlucoGuide uses a US-based, self-reported survey outcome and has not been clinically validated for diagnosis or for use with the Vietnamese population. AI assistance is not clinical review, clinical validation, or professional medical advice.

## 5. Declaration status

This appendix is a draft for group completion. It does not claim that every group member has independently verified the code or results, or that a healthcare professional has reviewed the application. The group should finalize this declaration only after the checks above have actually been completed.

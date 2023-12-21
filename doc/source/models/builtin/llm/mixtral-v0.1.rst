.. _models_llm_mixtral-v0.1:

========================================
mixtral-v0.1
========================================

- **Context Length:** 32768
- **Model Name:** mixtral-v0.1
- **Languages:** en, fr, it, de, es
- **Abilities:** generate
- **Description:** The Mixtral-8x7B Large Language Model (LLM) is a pretrained generative Sparse Mixture of Experts.

Specifications
^^^^^^^^^^^^^^


Model Spec 1 (pytorch, 46_7 Billion)
++++++++++++++++++++++++++++++++++++++++

- **Model Format:** pytorch
- **Model Size (in billions):** 46_7
- **Quantizations:** 4-bit, 8-bit, none
- **Model ID:** mistralai/Mixtral-8x7B-v0.1

Execute the following command to launch the model, remember to replace ``${quantization}`` with your
chosen quantization method from the options listed above::

   xinference launch --model-name mixtral-v0.1 --size-in-billions 46_7 --model-format pytorch --quantization ${quantization}


Model Spec 2 (ggufv2, 46_7 Billion)
++++++++++++++++++++++++++++++++++++++++

- **Model Format:** ggufv2
- **Model Size (in billions):** 46_7
- **Quantizations:** Q2_K, Q3_K_M, Q4_0, Q4_K_M, Q5_0, Q5_K_M, Q6_K, Q8_0
- **Model ID:** TheBloke/Mixtral-8x7B-v0.1-GGUF

Execute the following command to launch the model, remember to replace ``${quantization}`` with your
chosen quantization method from the options listed above::

   xinference launch --model-name mixtral-v0.1 --size-in-billions 46_7 --model-format ggufv2 --quantization ${quantization}


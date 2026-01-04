"""
Patch para aplicar hierarquia de headers automaticamente em TODOS os casos. 
"""
import logging
from functools import wraps

_log = logging. getLogger(__name__)


def apply_hierarchy_patch():
    """
    Substitui a função process_export_results do jobkit para injetar
    o pós-processamento de hierarquia (H1, H2, H3.. .) antes de salvar os arquivos.
    """
    try:
        from hierarchical. postprocessor import ResultPostprocessor
        from docling. datamodel. document import ConversionStatus
        import docling_jobkit. convert.results as results_module
    except ImportError as e:
        _log.warning(f"Could not import required modules for hierarchy patch: {e}")
        _log.warning("Header hierarchy will NOT be applied.  Install docling-hierarchical-pdf.")
        return

    # Guarda a referência original
    original_process_export_results = results_module.process_export_results

    @wraps(original_process_export_results)
    def patched_process_export_results(task, conv_results, work_dir):
        # 1. O conv_results original é um iterador (lazy).
        # Precisamos materializá-lo em uma lista para poder modificar os objetos
        # DoclingDocument dentro dele antes de passá-los para a exportação.
        results_list = list(conv_results)

        processed_count = 0

        # 2. Itera sobre os resultados e aplica a correção hierárquica
        for conv_res in results_list:
            if conv_res.status == ConversionStatus. SUCCESS:
                try:
                    # O postprocessor modifica o conv_res.document in-place (na memória)
                    processor = ResultPostprocessor(conv_res)
                    processor.process()
                    processed_count += 1
                except Exception as e:
                    _log.warning(
                        f"Error applying hierarchical post-processing to "
                        f"{conv_res.input. file. name}: {e}"
                    )

        if processed_count > 0:
            _log.info(f"Hierarchical structure applied to {processed_count} document(s).")

        # 3. Chama a função original do jobkit passando a nossa lista já modificada
        # A função original aceita Iterable, então uma list funciona perfeitamente.
        return original_process_export_results(task, results_list, work_dir)

    # Aplica o Monkey Patch
    results_module.process_export_results = patched_process_export_results
    _log. info("Hierarchy patch applied: docling-serve will now fix header levels.")


def patch_chunking_module():
    """
    Também aplica o patch no módulo de chunking, caso você use o endpoint de chunks.
    """
    try:
        from hierarchical.postprocessor import ResultPostprocessor
        from docling.datamodel.document import ConversionStatus
        import docling_jobkit.convert.chunking as chunking_module
    except ImportError: 
        return

    original_process_chunk_results = chunking_module.process_chunk_results

    @wraps(original_process_chunk_results)
    def patched_process_chunk_results(task, conv_results, work_dir):
        results_list = list(conv_results)

        for conv_res in results_list:
            if conv_res. status == ConversionStatus.SUCCESS: 
                try:
                    ResultPostprocessor(conv_res).process()
                except Exception as e:
                    _log.warning(f"Error in hierarchy patch for chunking: {e}")

        return original_process_chunk_results(task, results_list, work_dir)

    chunking_module.process_chunk_results = patched_process_chunk_results
    _log.info("Hierarchy patch also applied to chunking module.")
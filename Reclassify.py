"""
Model exported as python.
Name : Reclassify
Group : 
With QGIS : 32807
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsExpression
import processing


class Reclassification(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('territoire', 'Territoire', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('bdd_usage_des_sols', 'BDD usage des sols', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('bdd_reclassification', 'BDD reclassification', defaultValue=None))
        self.addParameter(QgsProcessingParameterString('categorie__nuancer_bdd_usage_des_sols', 'Categorie à nuancer (BDD usage des sols)', multiLine=False, defaultValue=''))
        self.addParameter(QgsProcessingParameterString('categorie_masque_bdd_reclassification', 'Categorie masque (BDD reclassification)', multiLine=False, defaultValue=''))
        self.addParameter(QgsProcessingParameterRasterDestination('ReclassDatabase', 'Reclass Database', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(9, model_feedback)
        results = {}
        outputs = {}

        # Tampon
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 1000,
            'END_CAP_STYLE': 0,  # Round
            'INPUT': parameters['territoire'],
            'JOIN_STYLE': 0,  # Round
            'MITER_LIMIT': 2,
            'SEGMENTS': 5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Tampon'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Decouper un raster selon une couche de masque
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': parameters['bdd_usage_des_sols'],
            'KEEP_RESOLUTION': False,
            'MASK': outputs['Tampon']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'SET_RESOLUTION': False,
            'SOURCE_CRS': None,
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:2154'),
            'TARGET_EXTENT': None,
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DecouperUnRasterSelonUneCoucheDeMasque'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Territoire reclass
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': parameters['bdd_reclassification'],
            'KEEP_RESOLUTION': False,
            'MASK': outputs['Tampon']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'SET_RESOLUTION': False,
            'SOURCE_CRS': None,
            'TARGET_CRS': None,
            'TARGET_EXTENT': None,
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['TerritoireReclass'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Warp (reproject)
        alg_params = {
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': outputs['TerritoireReclass']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'RESAMPLING': 0,  # Nearest Neighbour
            'SOURCE_CRS': None,
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:2154'),
            'TARGET_EXTENT': None,
            'TARGET_EXTENT_CRS': None,
            'TARGET_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['WarpReproject'] = processing.run('gdal:warpreproject', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # r.reclass classification
        alg_params = {
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'input': outputs['WarpReproject']['OUTPUT'],
            'rules': '',
            'txtrules': QgsExpression(" @categorie_masque_bdd_reclassification + ' = ' + @categorie_masque_bdd_reclassification + ' New category\\n* = NULL'").evaluate(),
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RreclassClassification'] = processing.run('grass7:r.reclass', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Polygonize (raster to vector)
        alg_params = {
            'BAND': 1,
            'EIGHT_CONNECTEDNESS': False,
            'EXTRA': '',
            'FIELD': 'New Cat',
            'INPUT': outputs['RreclassClassification']['output'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PolygonizeRasterToVector'] = processing.run('gdal:polygonize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Couper Raster de reclass
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': outputs['DecouperUnRasterSelonUneCoucheDeMasque']['OUTPUT'],
            'KEEP_RESOLUTION': False,
            'MASK': outputs['PolygonizeRasterToVector']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'SET_RESOLUTION': False,
            'SOURCE_CRS': None,
            'TARGET_CRS': None,
            'TARGET_EXTENT': None,
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CouperRasterDeReclass'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # r.reclass class 2
        alg_params = {
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'input': outputs['CouperRasterDeReclass']['OUTPUT'],
            'rules': '',
            'txtrules': QgsExpression(" @categorie__nuancer_bdd_usage_des_sols + ' = ' +   @categorie_masque_bdd_reclassification + ' New cat\\n* = NULL'").evaluate(),
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['RreclassClass2'] = processing.run('grass7:r.reclass', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Merge
        alg_params = {
            'DATA_TYPE': 5,  # Float32
            'EXTRA': '',
            'INPUT': [outputs['DecouperUnRasterSelonUneCoucheDeMasque']['OUTPUT'],outputs['RreclassClass2']['output']],
            'NODATA_INPUT': None,
            'NODATA_OUTPUT': None,
            'OPTIONS': '',
            'PCT': False,
            'SEPARATE': False,
            'OUTPUT': parameters['ReclassDatabase']
        }
        outputs['Merge'] = processing.run('gdal:merge', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['ReclassDatabase'] = outputs['Merge']['OUTPUT']
        return results

    def name(self):
        return 'Reclassification'

    def displayName(self):
        return 'Reclassification'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return Reclassification()

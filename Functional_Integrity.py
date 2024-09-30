"""
Model exported as python.
Name : Functional Integrity
Group : 
With QGIS : 32807
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsExpression
import processing


class IntgritFonctionnelle(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('territoire', 'Territoire', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('bdd_usage_des_sols', 'BDD usage des sols', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('taille_des_zones_de_convolution_en_m', 'Taille des zones de convolution (en m)', type=QgsProcessingParameterNumber.Double, defaultValue=1000))
        self.addParameter(QgsProcessingParameterNumber('taille_maximale_des_pixels_de_la_bdd_en_m', 'Taille maximale des pixels de la BDD (en m)', type=QgsProcessingParameterNumber.Double, minValue=1, defaultValue=None))
        self.addParameter(QgsProcessingParameterString('raster_values_defined_as_non_seminatural_0__eg_40_50_1402__', 'Raster values defined as NON (semi-)natural (0)  e.g. 40 50 1402 ; *', multiLine=False, defaultValue='*'))
        self.addParameter(QgsProcessingParameterString('raster_values_defined_as_null_no_data_eg_60_70_80__60_thru_80__', 'Raster values defined as NULL (no data) e.g. 60 70 80 ; 60 thru 80 ; *', multiLine=False, defaultValue='*'))
        self.addParameter(QgsProcessingParameterString('raster_values_defined_as_seminatural_1_eg_10_20_30_90_95_100__10_thru_30__', 'Raster values defined as (semi-)natural (1) e.g. 10 20 30 90 95 100 ; 10 thru 30 ; *', multiLine=False, defaultValue='*'))
        self.addParameter(QgsProcessingParameterRasterDestination('DatabaseTerritory', 'Database Territory', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('FunctionalIntegrityTerritory', 'Functional Integrity Territory', createByDefault=True, defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterDestination('SnTerritory', 'SN Territory', createByDefault=True, defaultValue=''))
        self.addParameter(QgsProcessingParameterRasterDestination('FunctionalTerritory', 'Functional Territory', createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(15, model_feedback)
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

        # Size of neighbourhood
        alg_params = {
            'CONDITION': '',
            'MESSAGE': QgsExpression("'Size of neighborhood: ' + to_string(2* to_int((  @taille_des_zones_de_convolution_en_m  / ( @taille_maximale_des_pixels_de_la_bdd_en_m *2))) + 1)").evaluate()
        }
        outputs['SizeOfNeighbourhood'] = processing.run('native:raisemessage', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # String concatenation 0
        alg_params = {
            'INPUT_1': parameters['raster_values_defined_as_non_seminatural_0__eg_40_50_1402__'],
            'INPUT_2': QgsExpression("' = 0 NO semi-natural\\n' + '* = NULL'").evaluate()
        }
        outputs['StringConcatenation0'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
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
            'OUTPUT': parameters['DatabaseTerritory']
        }
        outputs['DecouperUnRasterSelonUneCoucheDeMasque'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['DatabaseTerritory'] = outputs['DecouperUnRasterSelonUneCoucheDeMasque']['OUTPUT']

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # String concatenation 1
        alg_params = {
            'INPUT_1': parameters['raster_values_defined_as_seminatural_1_eg_10_20_30_90_95_100__10_thru_30__'],
            'INPUT_2': QgsExpression("' = 1 semi-natural\\n'").evaluate()
        }
        outputs['StringConcatenation1'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # String concatenation
        alg_params = {
            'INPUT_1': outputs['StringConcatenation1']['CONCATENATION'],
            'INPUT_2': outputs['StringConcatenation0']['CONCATENATION']
        }
        outputs['StringConcatenation'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # String concatenation no data
        alg_params = {
            'INPUT_1': parameters['raster_values_defined_as_null_no_data_eg_60_70_80__60_thru_80__'],
            'INPUT_2': QgsExpression("' = -1 no data\\n' + '* = NULL'").evaluate()
        }
        outputs['StringConcatenationNoData'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # r.reclass 0
        alg_params = {
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'input': outputs['DecouperUnRasterSelonUneCoucheDeMasque']['OUTPUT'],
            'rules': '',
            'txtrules': outputs['StringConcatenation']['CONCATENATION'],
            'output': parameters['SnTerritory']
        }
        outputs['Rreclass0'] = processing.run('grass7:r.reclass', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['SnTerritory'] = outputs['Rreclass0']['output']

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Database nomenclature
        alg_params = {
            'CONDITION': '',
            'MESSAGE': outputs['StringConcatenation']['CONCATENATION']
        }
        outputs['DatabaseNomenclature'] = processing.run('native:raisemessage', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # r.neighbors
        alg_params = {
            '-a': False,
            '-c': True,
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'gauss': None,
            'input': outputs['Rreclass0']['output'],
            'method': 0,  # average
            'quantile': '',
            'selection': None,
            'size': QgsExpression('2* to_int((  @taille_des_zones_de_convolution_en_m  / ( @taille_maximale_des_pixels_de_la_bdd_en_m *2))) + 1').evaluate(),
            'weight': '',
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rneighbors'] = processing.run('grass7:r.neighbors', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # r.reclass 1
        alg_params = {
            'GRASS_RASTER_FORMAT_META': '',
            'GRASS_RASTER_FORMAT_OPT': '',
            'GRASS_REGION_CELLSIZE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'input': outputs['DecouperUnRasterSelonUneCoucheDeMasque']['OUTPUT'],
            'rules': '',
            'txtrules': outputs['StringConcatenationNoData']['CONCATENATION'],
            'output': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Rreclass1'] = processing.run('grass7:r.reclass', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Polygonize (raster to vector)
        alg_params = {
            'BAND': 1,
            'EIGHT_CONNECTEDNESS': False,
            'EXTRA': '',
            'FIELD': 'Terr',
            'INPUT': outputs['Rreclass1']['output'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['PolygonizeRasterToVector'] = processing.run('gdal:polygonize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Difference
        alg_params = {
            'GRID_SIZE': None,
            'INPUT': parameters['territoire'],
            'OVERLAY': outputs['PolygonizeRasterToVector']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Difference'] = processing.run('native:difference', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Clip raster by mask layer Final
        alg_params = {
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'DATA_TYPE': 0,  # Use Input Layer Data Type
            'EXTRA': '',
            'INPUT': outputs['Rneighbors']['output'],
            'KEEP_RESOLUTION': False,
            'MASK': outputs['Difference']['OUTPUT'],
            'MULTITHREADING': False,
            'NODATA': None,
            'OPTIONS': '',
            'SET_RESOLUTION': False,
            'SOURCE_CRS': None,
            'TARGET_CRS': None,
            'TARGET_EXTENT': None,
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'OUTPUT': parameters['FunctionalIntegrityTerritory']
        }
        outputs['ClipRasterByMaskLayerFinal'] = processing.run('gdal:cliprasterbymasklayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['FunctionalIntegrityTerritory'] = outputs['ClipRasterByMaskLayerFinal']['OUTPUT']

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Reclassify by table
        alg_params = {
            'DATA_TYPE': 5,  # Float32
            'INPUT_RASTER': outputs['ClipRasterByMaskLayerFinal']['OUTPUT'],
            'NODATA_FOR_MISSING': False,
            'NO_DATA': -9999,
            'RANGE_BOUNDARIES': 2,  # min <= value <= max
            'RASTER_BAND': 1,
            'TABLE': ['0','0.24999','0','0.25','1','1'],
            'OUTPUT': parameters['FunctionalTerritory']
        }
        outputs['ReclassifyByTable'] = processing.run('native:reclassifybytable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['FunctionalTerritory'] = outputs['ReclassifyByTable']['OUTPUT']
        return results

    def name(self):
        return 'Intégrité fonctionnelle'

    def displayName(self):
        return 'Intégrité fonctionnelle'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return IntgritFonctionnelle()

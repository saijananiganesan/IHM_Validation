###################################
# Script : 
# 1) Contains Base class to 
# generate specific information 
# from mmcif files
# 2) Contains infromation for 
#  entry composition section
#
# ganesans - Salilab - UCSF
# ganesans@salilab.org
###################################

import ihm
import ihm.reader
import pandas as pd
import glob
import os
import numpy as np
import re
from collections import defaultdict
from validation import utility
from io import StringIO, BytesIO


#########################
#Get information from IHM reader
#########################

class get_input_information(object):
    def __init__(self,mmcif_file):
        self.mmcif_file = mmcif_file
        self.datasets = {}
        self.entities = {}
        self.model = ihm.model.Model
        self.system, = ihm.reader.read(open(self.mmcif_file),
                                  model_class=self.model)
        
    def get_databases(self):
        """ get all datasets from the mmcif file"""
        dbs=self.system.orphan_datasets
        return dbs

    def get_id(self):
        """ get id from model name, eg: PDBDEV_00XX will be PDBDEV00XX"""
        if self.system.id == 'model':
            id=self.get_id_from_entry()
        else:
            id=self.system.id.split('_')[0]+self.system.id.split('_')[1]
        return id

    def get_id_from_entry(self)->str:
        """ get id name from entry"""
        sf=open(self.mmcif_file,'r')
        for ind,ln in enumerate(sf.readlines()):
            line =ln.strip().split(' ')
            if '_entry' in line[0]:
                entry_init=line[-1]
                entry=entry_init.split('_')[0]+entry_init.split('_')[1]
        return entry

    def get_title(self)->str:
        """get title from citations """
        cit=self.system.citations
        title=cit[0].title
        return title

    def get_authors(self)->str:
        """get names of authors from citations """
        cit=self.system.citations
        aut=cit[0].authors
        for ind in range(0,len(aut)):
            if ind==0:
                authors=str(aut[ind])
            else:
                authors+=';'+str(aut[ind])
        return authors

    def get_struc_title(self)->str:
        """get name of molecule"""
        strc=self.system.title
        if strc is None:
            entities=self.system.entities
            mol_name=entities.description
        else:
            mol_name=strc
        return mol_name
    
    def check_sphere(self):
        """check resolution of structure,returns 0 if its atomic and 1 if the model is multires"""
        spheres=[len(b._spheres) for i in self.system.state_groups for j in i for a in j for b in a]
        if 0 not in spheres:
            return 1
        else:
            return 0 

    def get_assembly_ID_of_models(self)->list:
        """Assembly info i.e. model assemblies in the file """
        assembly_id=[b.assembly._id for i in self.system.state_groups for j in i for a in j for b in a]
        return assembly_id

    def get_representation_ID_of_models(self)->list:
        """Number of representations in model """
        representation_id=[b.representation._id for i in self.system.state_groups for j in i for a in j for b in a]
        return representation_id

    def get_model_names(self)->list:
        """ Names of models"""
        model_name1=[a.name for i in self.system.state_groups for j in i for a in j]
        model_name2=[b.name for i in self.system.state_groups for j in i for a in j for b in a]
        if len(model_name1)==len(model_name2):
            model_name =[str(t[0])+'/'+str(t[1]) for t in zip(model_name1,model_name2)]
        else:
            model_name=model_name2
        return model_name
    
    def get_model_assem_dict(self)->dict:
        """Map models to assemblies """
        model_id=map(int,[b._id for i in self.system.state_groups for j in i for a in j for b in a])
        assembly_id=map(int,self.get_assembly_ID_of_models())
        model_assembly=dict(zip(model_id,assembly_id))
        return model_assembly

    def get_model_rep_dict(self)->dict:
        """Map models to representations 
        useful especially for multi-state systems"""
        model_id=map(int,[b._id for i in self.system.state_groups for j in i for a in j for b in a])
        rep_id=map(int,self.get_representation_ID_of_models())
        model_rep=dict(zip(model_id,rep_id))
        return model_rep

    def get_number_of_models(self)->int:
        """ Get total number of models """
        models=[b._id for i in self.system.state_groups for j in i for a in j for b in a]
        return len(models)

    def get_residues(self,asym):
        """Get residues per chain """
        if asym.seq_id_range[0] is not None:
            residues=asym.seq_id_range[1]-asym.seq_id_range[0]+1
        elif asym.seq_id_range[0] is None:
            residues='None listed'
        return residues
    
    def get_composition(self)->dict:
        """Get composition dictionary"""
        entry_comp={'Model ID':[],'Subunit number':[],'Subunit ID':[],
                    'Subunit name':[],'Chain ID':[],
                    'Total residues':[]}
        for i,j in self.get_model_assem_dict().items():
            for m in self.system.orphan_assemblies:
                if int(m._id)==int(j):
                    count=0
                    for n in m:
                        try:
                            count += 1
                            entry_comp['Model ID'].append(i)
                            entry_comp['Subunit number'].append(count)
                            entry_comp['Subunit ID'].append(n.entity._id)
                            entry_comp['Subunit name'].append(str(n.entity.description))
                            entry_comp['Chain ID'].append(n._id)
                            entry_comp['Total residues'].append(self.get_residues(n))
                        except AttributeError:
                            break
        return entry_comp

    def get_protocol_number(self)->int:
        """ number of protocols/methods used to create model"""
        return len(self.system.orphan_protocols)

    def get_sampling(self)->dict:
        """ sampling composition/details """
        sampling_comp={'Step number':[], 'Protocol ID':[],'Method name':[],'Method type':[], \
                        'Number of computed models':[],'Multi state modeling':[], \
                        'Multi scale modeling':[]}
        for prot in self.system.orphan_protocols:
            for step in prot.steps:
                sampling_comp['Step number'].append(step._id)
                sampling_comp['Multi state modeling'].append(str(step.multi_state))
                sampling_comp['Multi scale modeling'].append(str(step.multi_scale))                
                sampling_comp['Protocol ID'].append(self.system.orphan_protocols.index(prot)+1)
                sampling_comp['Method name'].append(step.method)
                sampling_comp['Method type'].append(step.name)
                sampling_comp['Number of computed models'].append(step.num_models_end)
        return sampling_comp

    def get_representation(self):
        """ get details on number of model composition based on 
        types of representation listed """
        representation_comp={'Chain ID':[],'Subunit name':[],'Rigid bodies':[],
                    'Non-rigid regions':[]}
        for rep in self.system.orphan_representations:
            #print (rep,rep[0].rigid,rep[0].asym_unit.seq_id_range,rep[0].asym_unit._id)
            print (["%s:%d-%d" % ((x.asym_unit._id,) + x.asym_unit.seq_id_range) for x in rep if not x.rigid])

    def get_RB_flex_dict(self)->(dict,dict,int,int):
        """ get RB and flexible segments from model information""" 
        RB=self.get_empty_chain_dict();RB_nos=[];all_nos=[];flex=self.get_empty_chain_dict()
        for rep in self.system.orphan_representations:
            for el in rep:
                all_nos.append(el.asym_unit.seq_id_range)
                if el.rigid and el.starting_model:
                    RB_nos.append(el.asym_unit.seq_id_range)
                    RB[el.starting_model.asym_unit._id].append([utility.format_tupple(el.asym_unit.seq_id_range),
                        utility.get_val_from_key(self.get_dataset_dict(),el.starting_model.dataset._id)])
                elif el.rigid and not el.starting_model:
                    RB_nos.append(el.asym_unit.seq_id_range)
                    RB[el.asym_unit._id].append([utility.format_tupple(el.asym_unit.seq_id_range),'None'])
                else:
                    flex[el.asym_unit._id].append([utility.format_tupple(el.asym_unit.seq_id_range)])
        return RB,flex,len(RB_nos),len(all_nos)      

    def get_number_of_assemblies(self)->int:
        return (len(self.system.orphan_assemblies))

    def get_number_of_entities (self)->int:
        return (len(self.system.entities))

    def get_number_of_chains(self)->int:
        """get number of chains per protein per assembly """
        used=[];assembly=defaultdict()
        lists= self.system.orphan_assemblies
        for ind,ass in enumerate(self.system.orphan_assemblies):
            chain=[]
            for el in ass:
                chain.append(el._id)
            assembly[ind]=chain
            unique=[used.append(x) for x in chain if x not in used]
        number_of_chains=[len(i) for i in assembly.values()]
        return number_of_chains

    def get_all_asym(self)->list:
        """ get all asym units"""
        parents=[(a._id,a.details,a.entity.description,a.entity._id,i) for i,a in enumerate(self.system.asym_units)]
        return parents

    def get_empty_chain_dict(self)->dict:
        empty_chain_dict=defaultdict()
        for ind,el in enumerate(self.system.asym_units):
            empty_chain_dict[el._id]=[]
        return empty_chain_dict

    def get_chain_subunit_dict(self)->dict:
        """ Get chains of subunits"""
        chain_subunit_dict=defaultdict()
        for ind,el in enumerate(self.system.asym_units):
            chain_subunit_dict[el._id]=el.details.split('.')[0]
        return chain_subunit_dict

    def get_residues_subunit_dict(self)->dict:
        """Get residues of chains in subunits"""
        residues_subunit_dict=defaultdict()
        for _,el in enumerate(self.system.asym_units):
            print (self.get_residues(el))
            residues_subunit_dict[el._id]=self.get_residues(el)
        return residues_subunit_dict

    def get_software_length(self)->int:
        lists=self.system.software
        if lists is None:
            return 0
        else:
            return len(lists)

    def get_software_comp (self)->dict:
        """get software composition to write out as a table"""
        software_comp={'ID':[],'Software name':[],'Software version':[],'Software classification':[],'Software location':[]}
        lists=self.system.software
        if len(lists)>0:
            for _ in lists:
                software_comp['ID'].append(_._id)
                software_comp['Software name'].append(_.name)
                software_comp['Software location'].append(_.location)
                if str(_.version) == '?':
                    vers='None'
                else:
                    vers=str(_.version)
                software_comp['Software version'].append(vers)
                software_comp['Software classification'].append(_.classification)
            final_software_composition=software_comp
        else:
            final_software_composition={}
        return final_software_composition

    def check_ensembles(self)->int:
        """check if ensembles exist"""
        return len(self.system.ensembles)

    def get_ensembles(self):
        """details on ensembles, if it exists"""
        if len(self.system.ensembles)>0:
            ensemble_comp={'Ensemble number':[],'Ensemble name':[],'Model ID':[],'Number of models':[],
                        'Clustering method': [], 'Clustering feature': [], 'Cluster precision':[]}
            for _ in self.system.ensembles:
                ensemble_comp['Ensemble number'].append(str(_._id))
                ensemble_comp['Ensemble name'].append(str(_.name))
                ensemble_comp['Model ID'].append(str(_.model_group._id))
                ensemble_comp['Number of models'].append(str(_.num_models))
                ensemble_comp['Clustering method'].append(str(_.clustering_method))
                ensemble_comp['Clustering feature'].append(str(_.clustering_feature))
                ensemble_comp['Cluster precision'].append(str(_.precision))
            return ensemble_comp
        else:
            return None

    def get_dataset_xl_info(self,id:int)->str:
        """Get dataset XL info given dataset ID"""
        restraints=self.get_restraints()
        return 'Linker name and number of cross-links: %s' % (restraints['Restraint info'][restraints['Dataset ID'].index(id)])
        

    def get_dataset_dict(self):
        """get dataset dictionary """
        dataset_dict=defaultdict()
        lists=self.system.orphan_datasets
        if len(lists)>0:
            for _ in lists:
                try:
                    loc=_.location.db_name
                except AttributeError as error:
                    loc=str('Not listed')
                try:
                    acc=_.location.access_code
                except AttributeError as error:
                    acc=str('None')
                dataset_dict[_._id]=str(_.data_type)+'/'+str(acc)
        return dataset_dict 

    def get_dataset_length(self)->int:
        lists=self.system.orphan_datasets
        if lists is None:
            return 0
        else:
            return len(lists)

    def get_dataset_comp (self)->dict:
        """detailed dataset composition"""
        dataset_comp={'ID':[],'Dataset type':[],'Database name':[],'Data access code':[]}
        lists=self.system.orphan_datasets
        if len(lists)>0:
            for _ in lists:
                try:
                    loc=_.location.db_name
                except AttributeError as error:
                    loc=str('Not listed')
                try:
                    acc=_.location.access_code
                except AttributeError as error:
                    acc=str('None')
                dataset_comp['ID'].append(_._id)
                #if i.data_type=='unspecified' and 'None' not in i.details:
                #    dataset_comp['Dataset type'].append(i.details)
                #else:
                dataset_comp['Dataset type'].append(_.data_type)
                dataset_comp['Database name'].append(str(loc))
                dataset_comp['Data access code'].append(acc)
                #print (dataset_comp)
        return dataset_comp

    def dataset_id_type_dic(self)->dict:
        """dataset id and data items"""
        dataset_dic=defaultdict
        if len(self.system.orphan_datasets)>0:
            for i in self.system.orphan_datasets:
                if i.data_type =='unspecified':
                    dataset_dic[str(i._id)]=str(i.details)
                else:
                    dataset_dic[str(i._id)]=str(i.data_type)
        return dataset_dic
        
    def get_restraints(self)->dict:
        """ get restraints table from cif file"""
        r=self.system.restraints
        restraints_comp={'ID':[],'Dataset ID':[],'Restraint type':[],'Restraint info':[]}
        for j,i in enumerate(r):
            restraints_comp['ID'].append(j+1)
            restraints_comp['Restraint type'].append(str(i.__class__.__name__))
            restraints_comp['Dataset ID'].append(str(i.dataset._id))
            if 'CrossLink' in str(i.__class__.__name__):
                restraints_comp['Restraint info'].append(str(i.linker.auth_name)+', '+str(len(i.experimental_cross_links))+' cross-links')
            if 'EM3D' in str(i.__class__.__name__):
                restraints_comp['Restraint info'].append(str(i.fitting_method)+ ', '+str(i.number_of_gaussians))
            if 'EM2D' in str(i.__class__.__name__):
                restraints_comp['Restraint info'].append('Number of micrographs: '+str(i.number_raw_micrographs)+','+' Image resolution: '+str(i.image_resolution))
            if 'SAS' in str(i.__class__.__name__):
                restraints_comp['Restraint info'].append('Assembly name: '+str(i.assembly.name)+' Fitting method: '+str(i.fitting_method)+ ' Multi-state: '+str(i.multi_state))
            if 'UpperBound' in str(i.__class__.__name__):

                restraints_comp['Restraint info'].append('Distance: '+str(i.distance))
            if 'Mutagenesis' in str(i.__class__.__name__):
                restraints_comp['Restraint info'].append('Details: '+str(i.details))
            if 'DerivedDistance' in str(i.__class__.__name__):
                dic=self.dataset_id_type_dic()
                ID=str(i.dataset._id)
                #restraints_comp['Restraint info'].append(dic[ID])
                if 'UpperBound' in str(i.distance.__class__.__name__):
                    restraints_comp['Restraint info'].append(('Upper Bound Distance: '+str(i.distance.distance)))
                else:
                    restraints_comp['Restraint info'].append(['restraint type '+ str(i.distance.__class__.__name__),dic[ID]])
        return restraints_comp 
    
    def get_dataset_details(self)->dict:
        """get information on dataset and databases"""
        dataset_comp={'ID':[],'Dataset type':[],'Database name':[],'Details':[]}
        lists=self.system.orphan_datasets
        if len(lists)>0:
            for i in lists:
                try:
                    loc=i.location.db_name
                except AttributeError as error:
                    loc=str('')
                try:
                    acc=i.location.access_code
                except AttributeError as error:
                    acc=str('Not listed')
                dataset_comp['ID'].append(i._id)
                if i.data_type=='unspecified' and i.details is not None:
                    dataset_comp['Dataset type'].append(i.details)
                else:
                    dataset_comp['Dataset type'].append(i.data_type)
                dataset_comp['Database name'].append(str(loc))
                if 'ComparativeModel' in str(i.__class__.__name__):
                    acc1='template PDB ID: '+ acc
                    dataset_comp['Details'].append(acc1)
                elif 'PDB' in str(i.__class__.__name__):
                    acc1='PDB ID: '+ acc
                    dataset_comp['Details'].append(acc1)
                elif 'CX' in str(i.__class__.__name__):
                    acc1=self.get_dataset_xl_info(i._id)
                    dataset_comp['Details'].append(acc1)
                elif 'EM' in str(i.__class__.__name__):
                    acc1='EMDB ID: '+acc
                    dataset_comp['Details'].append(acc1)
                else:
                    dataset_comp['Details'].append(acc)
                    
        return dataset_comp
    
    def get_atomic_coverage(self)->str:
        """Measure amount of atomic residues"""
        for _ in self.system.orphan_representations:
            if self.check_sphere()==1:
                flex=sum([int(x.asym_unit.seq_id_range[1])-int(x.asym_unit.seq_id_range[0])+1 for x in _ if not x.rigid])
                rigid=sum([int(x.asym_unit.seq_id_range[1])-int(x.asym_unit.seq_id_range[0])+1 for x in _ if x.rigid])
                percentage=str(round(rigid/(rigid+flex)*100))+'%'
            else:
                percentage='100%'
        return percentage

    def check_for_sas(self,dataset:dict)->bool:
        """check if sas is in the dataset"""
        dataset=self.get_dataset_comp()
        data_type=dataset['Dataset type']
        database=dataset['Database name']
        if 'SAS' in str(data_type) and 'SAS' in str(database):
            return True
        else:
            return False

    def check_for_cx(self,dataset:dict)->bool:
        """check if CX-XL is in the dataset"""
        dataset=self.get_dataset_comp()
        data_type=dataset['Dataset type']
        if 'CX' in str(data_type):
            return True
        else:
            return False

    def check_for_em(self,dataset:dict)->bool:
        """check if em is in the dataset"""
        dataset=self.get_dataset_comp()
        data_type=dataset['Dataset type']
        if 'EM' in str(data_type):
            return True
        else:
            return False

    def mmcif_get_lists(self,filetemp=None)->(list,dict,dict,list):
        """function to help re-write mmcif file for molprobity
        this function reads the atom_site dictionary terms and returns a list"""
        if filetemp is None:
            file=open(self.mmcif_file,'r')
        else:
            file=filetemp
            filetemp.seek(0)
        all_lines=[]
        for i,j in enumerate(file.readlines()):
            all_lines.append(j.strip().split())
        atom_site={}
        atoms={}
        before_atom_site=[]
        after_atom=[]
        for i,j in enumerate(all_lines):
            if len(j)>0 and '_atom_site.' in j[0]:
                if len(before_atom_site)==0:
                    before_atom_site=all_lines[:i+1]
                atom_site[i]=j[0]
            elif ('_atom_site.B_iso_or_equiv' not in list(atom_site.values())) and len(list(atom_site.values()))>0:
                atom_site[i]='_atom_site.B_iso_or_equiv'
            elif ('_atom_site.occupancy' not in list(atom_site.values())) and len(list(atom_site.values()))>0 :
                atom_site[i]='_atom_site.occupancy'
        total_list=list(atom_site.values())
        index_biso=total_list.index('_atom_site.B_iso_or_equiv')
        index_occu=total_list.index('_atom_site.occupancy')
        for i,j in enumerate(all_lines):
            if len(j)> 0 and ('ATOM' in j[0] or 'HETATM' in j[0]) and  (i > list(atom_site.keys())[-1]):
                if len(j)<=index_occu:
                    j.extend(['1'])
                elif j[index_occu]=='.':
                    j[index_occu]='0.67'
                if len(j)<=index_biso:
                    j.extend(['1'])
                elif j[index_biso]=='.':
                    j[index_biso]='0.00'
                atoms[i]=j
            elif len(j)> 0 and  (i > list(atom_site.keys())[-1]):
                if len(after_atom)==0:
                    after_atom=all_lines[i:]
        return before_atom_site,atom_site,atoms,after_atom

    def rewrite_mmcif(self):
        """ This function writes a temporary mmcif file that can be parsed by molprobity
        after checking occupancy and b-iso parameters """
        before_atom_site,atom_site,atoms,after_atom=self.mmcif_get_lists()
        if os.path.isfile('test.cif'):
            os.remove('test.cif')
        file_re=open('test.cif','w')
        for i, j in enumerate(before_atom_site[:-1]):
            file_re.write(' '.join(j)+'\n')
        for i, j in atom_site.items():
            file_re.write(''.join(j)+'\n')
        for i,j in atoms.items():
            file_re.write(' '.join(j)+'\n')
        for i,j in enumerate(after_atom):
            file_re.write(' '.join(j)+'\n')





import os
import spacy
import re
from collections import defaultdict

class KnowledgeGraphBuilder:
    def __init__(self, extracted_content_dir="extracted_content", output_dir="knowledge_graph"):
        self.extracted_content_dir = extracted_content_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.nlp = spacy.load("en_core_web_sm")
        self.entities = defaultdict(set) # {entity_type: {entity_name, ...}}
        self.relationships = defaultdict(list) # { (entity1, relation, entity2), ...}

    def _extract_entities(self, text):
        doc = self.nlp(text)
        extracted = defaultdict(set)
        for ent in doc.ents:
            # Filter for relevant entity types
            if ent.label_ in ["ORG", "GPE", "LOC", "DATE", "PRODUCT", "EVENT", "NORP", "FAC", "PERSON"]:
                extracted[ent.label_].add(ent.text.strip())
        return extracted

    def _extract_relationships(self, text, doc_entities):
        # This is a simplified approach. More advanced techniques like dependency parsing
        # or OpenIE would be used for robust relationship extraction.
        # For now, we look for co-occurrence and simple patterns.
        relationships_found = []

        # Simple co-occurrence based relationship extraction
        # This is a placeholder and needs significant improvement for real-world use
        for entity_type1, entities1 in doc_entities.items():
            for entity1_text in entities1:
                for entity_type2, entities2 in doc_entities.items():
                    for entity2_text in entities2:
                        if entity1_text != entity2_text and entity1_text in text and entity2_text in text:
                            # Example: If both a satellite and a product are in the text
                            if entity_type1 == "PRODUCT" and entity_type2 == "ORG":
                                if f"{entity1_text} from {entity2_text}" in text or f"{entity1_text} by {entity2_text}" in text:
                                    relationships_found.append((entity1_text, "PRODUCED_BY", entity2_text))
                            elif entity_type1 == "ORG" and entity_type2 == "PERSON":
                                if f"{entity2_text}, {entity1_text}" in text or f"{entity2_text} from {entity1_text}" in text:
                                    relationships_found.append((entity2_text, "AFFILIATED_WITH", entity1_text))
                            # Add more specific patterns based on content analysis
                            # For instance, if "INSAT-3DR is identical to INSAT-3D"
                            if "identical to" in text and entity_type1 == "PRODUCT" and entity_type2 == "PRODUCT":
                                if f"{entity1_text} is identical to {entity2_text}" in text:
                                    relationships_found.append((entity1_text, "IDENTICAL_TO", entity2_text))

        return relationships_found

    def process_text_file(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        doc_entities = self._extract_entities(content)
        for ent_type, ents in doc_entities.items():
            for ent_text in ents:
                self.entities[ent_type].add(ent_text)
        
        doc_relationships = self._extract_relationships(content, doc_entities)
        for rel in doc_relationships:
            self.relationships["general"].append(rel)

    def process_tables(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Simple table parsing for now, needs more sophisticated logic for complex tables
        # This part will be heavily dependent on the actual table structures
        lines = content.split("\n")
        current_table = []
        for line in lines:
            if line.startswith("--- Table"):
                if current_table:
                    self._parse_table_data(current_table)
                    current_table = []
                continue
            if line.strip():
                current_table.append(line.strip())
        if current_table:
            self._parse_table_data(current_table)

    def _parse_table_data(self, table_lines):
        # This is a very basic table parser. Needs to be customized for each table type.
        # Example: For the "Tools" table, extract Name, Platform, Download URL
        if not table_lines: return

        # Heuristic to identify header row (e.g., contains "Name", "Platform", "Download URL")
        header = table_lines[0].split("\t")
        if "Platform" in header and "Download URL" in header:
            for row_idx, row_line in enumerate(table_lines[1:]):
                row_data = row_line.split("\t")
                if len(row_data) >= len(header):
                    tool_name = row_data[header.index("Platform")] if "Platform" in header else f"Tool_{row_idx}"
                    download_url = row_data[header.index("Download URL")] if "Download URL" in header else ""
                    if tool_name and download_url:
                        self.entities["Software/Tool"].add(tool_name)
                        self.relationships["Software/Tool"].append((tool_name, "HAS_DOWNLOAD_URL", download_url))
        
        # Example: For the "Metadata" table, extract key-value pairs
        if "Core Metadata Elements" in header and "Definition" in header:
            for row_idx, row_line in enumerate(table_lines[1:]):
                row_data = row_line.split("\t")
                if len(row_data) >= len(header):
                    metadata_element = row_data[header.index("Core Metadata Elements")] if "Core Metadata Elements" in header else ""
                    definition = row_data[header.index("Definition")] if "Definition" in header else ""
                    if metadata_element and definition:
                        # This can be refined to create specific entities/relationships
                        self.relationships["Metadata"].append((metadata_element, "HAS_DEFINITION", definition))


    def build_graph(self):
        for root, _, files in os.walk(self.extracted_content_dir):
            for file in files:
                filepath = os.path.join(root, file)
                if filepath.endswith(".txt") and not filepath.endswith("_tables.txt"):
                    print(f"Processing text file: {filepath}")
                    self.process_text_file(filepath)
                elif filepath.endswith("_tables.txt"):
                    print(f"Processing table file: {filepath}")
                    self.process_tables(filepath)
        
        # Save extracted entities and relationships
        with open(os.path.join(self.output_dir, "entities.txt"), "w", encoding="utf-8") as f:
            for ent_type, ents in self.entities.items():
                f.write(f"--- {ent_type} ---\n")
                for ent in ents:
                    f.write(f"{ent}\n")
        
        with open(os.path.join(self.output_dir, "relationships.txt"), "w", encoding="utf-8") as f:
            for rel_type, rels in self.relationships.items():
                f.write(f"--- {rel_type} Relationships ---\n")
                for rel in rels:
                    f.write(f"{rel}\n")

        print("Knowledge graph building complete. Entities and relationships saved.")

if __name__ == "__main__":
    # This part will be executed when the script is run directly
    # Ensure 'extracted_content' directory exists and contains scraped data
    kg_builder = KnowledgeGraphBuilder()
    kg_builder.build_graph()


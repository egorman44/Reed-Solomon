class EncodedMessageComparator:
    def __init__(self):
        # Stores name → message mapping
        self.encoded_messages = {}

    def add_msg(self, name: str, message: list[int]):
        """
        Add an encoded message under a specific name.

        :param name: Descriptive name (e.g., 'encode', 'encode_seq', 'encode_par')
        :param message: List of encoded symbols
        """
        self.encoded_messages[name] = message

    def compare(self):
        """
        Compare all added encoded messages.
        Raises an error if there's a length mismatch or symbol mismatch.
        Prints mismatch positions and values for easier debugging.
        """
        if len(self.encoded_messages) < 2:
            raise ValueError("At least two encoded messages must be added for comparison.")

        # Step 1: Check all lengths are equal
        lengths = {name: len(msg) for name, msg in self.encoded_messages.items()}
        if len(set(lengths.values())) != 1:
            print("Length mismatch detected:")
            for name, length in lengths.items():
                print(f"  {name}: length = {length}")
            raise ValueError("Encoded messages have different lengths.")

        # Step 2: Symbol-by-symbol comparison
        names = list(self.encoded_messages.keys())
        base_name = names[0]
        base_msg = self.encoded_messages[base_name]
        mismatches = []

        for i in range(len(base_msg)):
            base_val = base_msg[i]
            for other_name in names[1:]:
                other_val = self.encoded_messages[other_name][i]
                if base_val != other_val:
                    mismatches.append((i, base_name, base_val, other_name, other_val))

        if mismatches:
            print("Mismatch detected at the following positions:")
            for i, n1, v1, n2, v2 in mismatches:
                print(f"  Position {i}: {n1}={v1} vs {n2}={v2}")
            raise ValueError("Encoded messages differ in content.")
        else:
            print("✅ All encoded messages match!")

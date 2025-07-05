/**
 * Class written by Zabi94
 * Feb 15, 2018
 * Distributed under MIT license
 * 
 * This class allows the installation of optifine via command line
 * This is not affiliated with Optifine
 */

package zabi.minecraft.ofb.loggers;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.PrintStream;

public class FileLoggerModifier extends AbstractLoggerModifier {
	
	File output;

	public FileLoggerModifier() {
		output = new File("of_install_0.log");
		int iteration = 1;
		while (output.exists()) {
			output = new File("of_install_"+iteration+".log");
			iteration++;
		}
	}
	
	@Override
	public PrintStream createNewStream() {
		try {
			output.createNewFile();
			return new PrintStream(new FileOutputStream(output));
		} catch (IOException e) {
			System.err.println("Error during log redirection, not logging");
			e.printStackTrace();
			return new PrintStream(new VoidLoggerModifier.NullOutputStream());
		}
	}

}

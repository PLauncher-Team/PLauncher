/**
 * Class written by Zabi94
 * Feb 15, 2018
 * Distributed under MIT license
 * 
 * This class allows the installation of optifine via command line
 * This is not affiliated with Optifine
 */

package zabi.minecraft.ofb.loggers;

import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintStream;

public class VoidLoggerModifier extends AbstractLoggerModifier {

	@Override
	public PrintStream createNewStream() {
		return new PrintStream(new NullOutputStream());
	}
	
	public static class NullOutputStream extends OutputStream {
		@Override
		public void write(int b) throws IOException {
		}
	}

}
